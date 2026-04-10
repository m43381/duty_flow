from access_control.services import AccessManager


def get_ruleset_for_user(user):
    access = AccessManager(user)
    return access.ruleset


def seed_rules(user, resource: str):
    access = AccessManager(user)

    if resource == "user":
        access.seed_default_user_rules()
    elif resource == "person":
        access.seed_default_person_rules()
    elif resource == "unit":
        access.seed_default_unit_rules()
    elif resource == "unit_type":
        access.seed_default_unit_type_rules()
    elif resource == "duty_type":
        access.seed_default_duty_type_rules()
    else:
        raise ValueError(f"Неизвестный ресурс: {resource}")

    return access.ruleset