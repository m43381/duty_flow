from access_control.models import AccessFieldRule, AccessRule
from access_control.services import AccessManager


class AccessControlService:
    USER_ACTIONS = [
        ("view", "Просмотр"),
        ("create", "Создание"),
        ("update", "Редактирование"),
        ("delete", "Удаление"),
        ("change_password", "Смена пароля"),
    ]

    USER_FIELDS = [
        ("username", "Логин"),
        ("first_name", "Имя"),
        ("last_name", "Фамилия"),
        ("email", "Email"),
        ("unit", "Подразделение"),
    ]

    USER_SCOPES = [
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
    def seed_user_rules(user):
        access = AccessManager(user)
        access.seed_default_user_rules()
        return access.ruleset

    @staticmethod
    def build_user_access_matrix(user, level: int):
        ruleset = AccessControlService.get_ruleset_for_user(user)

        action_rows = []
        for action_code, action_label in AccessControlService.USER_ACTIONS:
            rule = (
                AccessRule.objects.filter(
                    ruleset=ruleset,
                    resource="user",
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
                "rule": rule,
            })

        field_rows = []
        for action_code, action_label in [("view", "Просмотр"), ("create", "Создание"), ("update", "Редактирование")]:
            fields_data = []

            existing_rules = {
                item.field_name: item
                for item in AccessFieldRule.objects.filter(
                    ruleset=ruleset,
                    resource="user",
                    action=action_code,
                    subject_level=level,
                    is_active=True,
                ).order_by("priority", "id")
            }

            for field_name, field_label in AccessControlService.USER_FIELDS:
                field_rule = existing_rules.get(field_name)
                fields_data.append({
                    "field_name": field_name,
                    "field_label": field_label,
                    "can_view": field_rule.can_view if field_rule else False,
                    "can_edit": field_rule.can_edit if field_rule else False,
                    "rule": field_rule,
                })

            field_rows.append({
                "action": action_code,
                "action_label": action_label,
                "fields": fields_data,
            })

        return {
            "ruleset": ruleset,
            "level": level,
            "action_rows": action_rows,
            "field_rows": field_rows,
            "scopes": AccessControlService.USER_SCOPES,
        }

    @staticmethod
    def save_user_access_matrix(user, level: int, post_data):
        ruleset = AccessControlService.get_ruleset_for_user(user)

        for action_code, _ in AccessControlService.USER_ACTIONS:
            allowed = post_data.get(f"action__{action_code}__allowed") == "on"
            scope = post_data.get(f"action__{action_code}__scope", "none")

            AccessRule.objects.update_or_create(
                ruleset=ruleset,
                resource="user",
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

        for action_code, _ in [("view", "Просмотр"), ("create", "Создание"), ("update", "Редактирование")]:
            for field_name, _ in AccessControlService.USER_FIELDS:
                can_view = post_data.get(f"field__{action_code}__{field_name}__view") == "on"
                can_edit = post_data.get(f"field__{action_code}__{field_name}__edit") == "on"

                AccessFieldRule.objects.update_or_create(
                    ruleset=ruleset,
                    resource="user",
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

        return ruleset