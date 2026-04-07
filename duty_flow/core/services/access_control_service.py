from access_control.models import AccessChoiceRule, AccessFieldRule, AccessRule
from access_control.services import AccessManager


class AccessControlService:
    RESOURCE_CONFIG = {
        "user": {
            "title": "Пользователи",
            "actions": [
                ("view", "Просмотр"),
                ("create", "Создание"),
                ("update", "Редактирование"),
                ("delete", "Удаление"),
                ("change_password", "Смена пароля"),
            ],
            "field_actions": [
                ("view", "Просмотр"),
                ("create", "Создание"),
                ("update", "Редактирование"),
            ],
            "choice_actions": [
                ("create", "Создание"),
                ("update", "Редактирование"),
            ],
            "fields": [
                ("username", "Логин"),
                ("first_name", "Имя"),
                ("last_name", "Фамилия"),
                ("email", "Email"),
                ("unit", "Подразделение"),
            ],
            "choice_fields": [
                ("unit", "Подразделение"),
            ],
        },
        "person": {
            "title": "Сотрудники",
            "actions": [
                ("view", "Просмотр"),
                ("create", "Создание"),
                ("update", "Редактирование"),
                ("delete", "Удаление"),
                ("manage_exemptions", "Управление освобождениями"),
                ("manage_clearances", "Управление допусками"),
            ],
            "field_actions": [
                ("view", "Просмотр"),
                ("create", "Создание"),
                ("update", "Редактирование"),
            ],
            "choice_actions": [
                ("create", "Создание"),
                ("update", "Редактирование"),
            ],
            "fields": [
                ("last_name", "Фамилия"),
                ("first_name", "Имя"),
                ("middle_name", "Отчество"),
                ("rank", "Звание"),
                ("unit", "Подразделение"),
            ],
            "choice_fields": [
                ("unit", "Подразделение"),
            ],
        },
    }

    SCOPES = [
        ("none", "Ничего"),
        ("own_unit", "Только своё подразделение"),
        ("descendants", "Только дочерние подразделения"),
        ("own_and_descendants", "Своё и дочерние подразделения"),
        ("all", "Все подразделения"),
    ]

    @staticmethod
    def get_ruleset_for_user(user):
        access = AccessManager(user)
        return access.ruleset

    @staticmethod
    def seed_rules(user, resource: str):
        access = AccessManager(user)
        if resource == "user":
            access.seed_default_user_rules()
        elif resource == "person":
            access.seed_default_person_rules()
        return access.ruleset

    @staticmethod
    def build_matrix(user, resource: str, level: int):
        ruleset = AccessControlService.get_ruleset_for_user(user)
        config = AccessControlService.RESOURCE_CONFIG[resource]

        action_rows = []
        for action_code, action_label in config["actions"]:
            rule = (
                AccessRule.objects.filter(
                    ruleset=ruleset,
                    resource=resource,
                    action=action_code,
                    subject_level=level,
                    is_active=True,
                )
                .order_by("priority", "id")
                .first()
            )

            action_rows.append({
                "action": action_code,
                "label": action_label,
                "allowed": rule.is_allowed if rule else False,
                "scope": rule.scope if rule else "none",
            })

        field_rows = []
        for action_code, action_label in config["field_actions"]:
            fields_data = []

            existing_rules = {
                item.field_name: item
                for item in AccessFieldRule.objects.filter(
                    ruleset=ruleset,
                    resource=resource,
                    action=action_code,
                    subject_level=level,
                    is_active=True,
                ).order_by("priority", "id")
            }

            for field_name, field_label in config["fields"]:
                field_rule = existing_rules.get(field_name)
                fields_data.append({
                    "field_name": field_name,
                    "field_label": field_label,
                    "can_view": field_rule.can_view if field_rule else False,
                    "can_edit": field_rule.can_edit if field_rule else False,
                })

            field_rows.append({
                "action": action_code,
                "action_label": action_label,
                "fields": fields_data,
            })

        choice_rows = []
        for action_code, action_label in config["choice_actions"]:
            fields_data = []

            existing_rules = {
                item.field_name: item
                for item in AccessChoiceRule.objects.filter(
                    ruleset=ruleset,
                    resource=resource,
                    action=action_code,
                    subject_level=level,
                    is_active=True,
                ).order_by("priority", "id")
            }

            for field_name, field_label in config["choice_fields"]:
                choice_rule = existing_rules.get(field_name)
                fields_data.append({
                    "field_name": field_name,
                    "field_label": field_label,
                    "scope": choice_rule.scope if choice_rule else "none",
                })

            choice_rows.append({
                "action": action_code,
                "action_label": action_label,
                "fields": fields_data,
            })

        return {
            "ruleset": ruleset,
            "resource": resource,
            "resource_title": config["title"],
            "level": level,
            "action_rows": action_rows,
            "field_rows": field_rows,
            "choice_rows": choice_rows,
            "scopes": AccessControlService.SCOPES,
        }

    @staticmethod
    def save_matrix(user, resource: str, level: int, post_data):
        ruleset = AccessControlService.get_ruleset_for_user(user)
        config = AccessControlService.RESOURCE_CONFIG[resource]

        for action_code, _ in config["actions"]:
            allowed = post_data.get(f"action__{action_code}__allowed") == "on"
            scope = post_data.get(f"action__{action_code}__scope", "none")

            AccessRule.objects.update_or_create(
                ruleset=ruleset,
                resource=resource,
                action=action_code,
                subject_level=level,
                priority=10,
                defaults={
                    "is_allowed": allowed,
                    "scope": scope,
                    "is_active": True,
                    "note": "Настроено через матрицу прав",
                },
            )

        for action_code, _ in config["field_actions"]:
            for field_name, _ in config["fields"]:
                can_view = post_data.get(f"field__{action_code}__{field_name}__view") == "on"
                can_edit = post_data.get(f"field__{action_code}__{field_name}__edit") == "on"

                AccessFieldRule.objects.update_or_create(
                    ruleset=ruleset,
                    resource=resource,
                    action=action_code,
                    subject_level=level,
                    field_name=field_name,
                    priority=10,
                    defaults={
                        "can_view": can_view,
                        "can_edit": can_edit,
                        "is_active": True,
                        "note": "Настроено через матрицу полей",
                    },
                )

        for action_code, _ in config["choice_actions"]:
            for field_name, _ in config["choice_fields"]:
                scope = post_data.get(f"choice__{action_code}__{field_name}__scope", "none")

                AccessChoiceRule.objects.update_or_create(
                    ruleset=ruleset,
                    resource=resource,
                    action=action_code,
                    subject_level=level,
                    field_name=field_name,
                    priority=10,
                    defaults={
                        "scope": scope,
                        "is_active": True,
                        "note": "Настроено через матрицу select/queryset",
                    },
                )

        return ruleset