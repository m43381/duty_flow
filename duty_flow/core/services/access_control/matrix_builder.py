from access_control.models import AccessChoiceRule, AccessFieldRule, AccessRule
from units.models import Unit, UnitType

from access_control.services.labels import build_unit_path_label
from .config import CHOICE_MODES, RESOURCE_CONFIG, SCOPES
from .ruleset import get_ruleset_for_user


def build_matrix(user, resource: str, level: int):
    if resource not in RESOURCE_CONFIG:
        raise ValueError(f"Неизвестный ресурс: {resource}")

    ruleset = get_ruleset_for_user(user)
    config = RESOURCE_CONFIG[resource]
    units = Unit.objects.select_related("parent", "unit_type").all().order_by("name")
    unit_types = UnitType.objects.all().order_by("level", "name")

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
            ).prefetch_related("units", "unit_types").order_by("priority", "id")
        }

        action_choice_fields = config["choice_fields"].get(action_code, [])

        for field_name, field_label in action_choice_fields:
            choice_rule = existing_rules.get(field_name)

            selected_unit_ids = list(choice_rule.units.values_list("id", flat=True)) if choice_rule else []
            selected_unit_type_ids = list(choice_rule.unit_types.values_list("id", flat=True)) if choice_rule else []

            if field_name in {"unit", "parent", "delegate_unit"}:
                mode_options = [
                    ("scope", "По scope"),
                    ("specific_units", "Только конкретные подразделения"),
                    ("scope_plus_units", "Scope + конкретные подразделения"),
                    ("all_values", "Все значения"),
                ]
            elif field_name == "unit_type":
                mode_options = [
                    ("all_values", "Все значения"),
                    ("specific_unit_types", "Только конкретные типы подразделений"),
                ]
            else:
                mode_options = CHOICE_MODES

            fields_data.append({
                "field_name": field_name,
                "field_label": field_label,
                "scope": choice_rule.scope if choice_rule else "none",
                "mode": choice_rule.mode if choice_rule else "scope",
                "mode_options": mode_options,
                "selected_unit_ids": selected_unit_ids,
                "selected_unit_type_ids": selected_unit_type_ids,
                "unit_options": [
                    {"id": unit.id, "label": build_unit_path_label(unit)}
                    for unit in units
                ] if field_name in {"unit", "parent", "delegate_unit"} else [],
                "unit_type_options": [
                    {"id": item.id, "label": f"{item.name} (уровень {item.level})"}
                    for item in unit_types
                ] if field_name == "unit_type" else [],
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
        "choice_modes": CHOICE_MODES,
    }