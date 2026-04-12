from django.contrib.auth.models import User

from access_control.services import AccessManager


SUPPORTED_RESOURCES = {
    "user": {
        "label": "Пользователи",
        "actions": ["view", "create", "update", "delete", "change_password"],
        "field_actions": ["view", "create", "update"],
        "choice_actions": ["create", "update"],
    },
    "person": {
        "label": "Сотрудники",
        "actions": ["view", "create", "update", "delete", "manage_exemptions", "manage_clearances"],
        "field_actions": ["view", "create", "update"],
        "choice_actions": ["create", "update", "manage_clearances"],
    },
    "unit": {
        "label": "Подразделения",
        "actions": ["view", "create", "update", "delete"],
        "field_actions": ["view", "create", "update"],
        "choice_actions": ["create", "update"],
    },
    "unit_type": {
        "label": "Типы подразделений",
        "actions": ["view", "create", "update", "delete"],
        "field_actions": ["view", "create", "update"],
        "choice_actions": [],
    },
    "duty_type": {
        "label": "Типы нарядов",
        "actions": ["view", "create", "update", "delete"],
        "field_actions": ["view", "create", "update"],
        "choice_actions": ["create", "update"],
    },
    "plan": {
        "label": "Планы нарядов",
        "actions": ["view", "create", "update", "delete", "manage_days", "accept_incoming"],
        "field_actions": ["view", "create", "update"],
        "choice_actions": ["manage_days"],
    },
    "assignment": {
        "label": "Назначения сотрудников",
        "actions": ["view", "assign", "unassign"],
        "field_actions": [],
        "choice_actions": [],
    },
}


def _get_choice_summary(access: AccessManager, resource: str, action: str):
    if resource == "user":
        if action == "create":
            units = access.allowed_units_for_user_creation()
            return [u.name for u in units]
        if action == "update":
            units = access.allowed_units_for_user_update()
            return [u.name for u in units]

    if resource == "person":
        if action == "create":
            units = access.allowed_units_for_person_creation()
            return [u.name for u in units]
        if action == "update":
            units = access.allowed_units_for_person_update()
            return [u.name for u in units]
        if action == "manage_clearances":
            duty_types = access.allowed_duty_types_for_clearance()
            return [d.name for d in duty_types]

    if resource == "unit":
        if action == "create":
            parents = access.allowed_parents_for_unit_creation()
            unit_types = access.allowed_unit_types_for_unit_creation()
            return {
                "parents": [u.name for u in parents],
                "unit_types": [ut.name for ut in unit_types],
            }
        if action == "update":
            parents = access.allowed_parents_for_unit_update()
            unit_types = access.allowed_unit_types_for_unit_update()
            return {
                "parents": [u.name for u in parents],
                "unit_types": [ut.name for ut in unit_types],
            }

    if resource == "duty_type":
        if action == "create":
            units = access.allowed_units_for_duty_type_creation()
            return [u.name for u in units]
        if action == "update":
            units = access.allowed_units_for_duty_type_update()
            return [u.name for u in units]

    return None


def build_access_diagnostics(target_user: User, resource: str):
    if resource not in SUPPORTED_RESOURCES:
        raise ValueError(f"Неизвестный ресурс: {resource}")

    access = AccessManager(target_user)
    config = SUPPORTED_RESOURCES[resource]

    profile = getattr(target_user, "profile", None)
    user_unit = getattr(profile, "unit", None)

    actions = []
    for action in config["actions"]:
        method_name = f"can_{resource}"
        if hasattr(access, method_name):
            allowed = getattr(access, method_name)(action)
        else:
            allowed = False
        actions.append({
            "action": action,
            "allowed": allowed,
        })

    visible_fields = []
    editable_fields = []
    for action in config["field_actions"]:
        visible_method = f"visible_{resource}_fields"
        editable_method = f"editable_{resource}_fields"

        visible = getattr(access, visible_method)(action) if hasattr(access, visible_method) else set()
        editable = getattr(access, editable_method)(action) if hasattr(access, editable_method) else set()

        visible_fields.append({
            "action": action,
            "fields": sorted(list(visible)),
        })
        editable_fields.append({
            "action": action,
            "fields": sorted(list(editable)),
        })

    choices = []
    for action in config["choice_actions"]:
        summary = _get_choice_summary(access, resource, action)
        choices.append({
            "action": action,
            "summary": summary,
        })

    return {
        "target_user": target_user,
        "resource": resource,
        "resource_label": config["label"],
        "ruleset": access.ruleset,
        "user_level": getattr(profile, "level", None),
        "user_unit": user_unit,
        "actions": actions,
        "visible_fields": visible_fields,
        "editable_fields": editable_fields,
        "choices": choices,
    }