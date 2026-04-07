from access_control.models import AccessChoiceRule, AccessFieldRule, AccessRule

from .config import RESOURCE_CONFIG, SCOPES
from .ruleset import get_ruleset_for_user


def build_matrix(user, resource: str, level: int):
    if resource not in RESOURCE_CONFIG:
        raise ValueError(f"Неизвестный ресурс: {resource}")

    ruleset = get_ruleset_for_user(user)
    config = RESOURCE_CONFIG[resource]

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
        "scopes": SCOPES,
    }