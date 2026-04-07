from access_control.models import AccessChoiceRule, AccessFieldRule, AccessRule

from .config import RESOURCE_CONFIG
from .ruleset import get_ruleset_for_user


def save_matrix(user, resource: str, level: int, post_data):
    if resource not in RESOURCE_CONFIG:
        raise ValueError(f"Неизвестный ресурс: {resource}")

    ruleset = get_ruleset_for_user(user)
    config = RESOURCE_CONFIG[resource]

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