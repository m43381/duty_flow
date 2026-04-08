from access_control.models import AccessChoiceRule, AccessFieldRule, AccessRule


def seed_default_user_rules(ruleset):
    default_rules = [
        (0, "view", True, "all", 10),
        (0, "create", True, "all", 10),
        (0, "update", True, "all", 10),
        (0, "delete", True, "all", 10),
        (0, "change_password", True, "all", 10),

        (1, "view", True, "own_and_descendants", 10),
        (1, "create", True, "own_and_descendants", 10),
        (1, "update", True, "own_and_descendants", 10),
        (1, "delete", False, "none", 10),
        (1, "change_password", True, "own_and_descendants", 10),

        (2, "view", True, "own_unit", 10),
        (2, "create", False, "none", 10),
        (2, "update", False, "none", 10),
        (2, "delete", False, "none", 10),
        (2, "change_password", False, "none", 10),
    ]

    for subject_level, action, is_allowed, scope, priority in default_rules:
        AccessRule.objects.update_or_create(
            ruleset=ruleset,
            resource="user",
            action=action,
            subject_level=subject_level,
            priority=priority,
            defaults={
                "is_allowed": is_allowed,
                "scope": scope,
                "is_active": True,
                "note": "Автозаполнение стартового набора",
            },
        )

    default_field_rules = [
        (0, "view", "username", True, False),
        (0, "view", "first_name", True, False),
        (0, "view", "last_name", True, False),
        (0, "view", "email", True, False),
        (0, "view", "unit", True, False),

        (0, "create", "username", True, True),
        (0, "create", "first_name", True, True),
        (0, "create", "last_name", True, True),
        (0, "create", "email", True, True),
        (0, "create", "unit", True, True),

        (0, "update", "username", True, True),
        (0, "update", "first_name", True, True),
        (0, "update", "last_name", True, True),
        (0, "update", "email", True, True),

        (1, "view", "username", True, False),
        (1, "view", "first_name", True, False),
        (1, "view", "last_name", True, False),
        (1, "view", "email", True, False),
        (1, "view", "unit", True, False),

        (1, "create", "username", True, True),
        (1, "create", "first_name", True, True),
        (1, "create", "last_name", True, True),
        (1, "create", "email", True, True),
        (1, "create", "unit", True, True),

        (1, "update", "username", True, True),
        (1, "update", "first_name", True, True),
        (1, "update", "last_name", True, True),
        (1, "update", "email", True, True),

        (2, "view", "username", True, False),
        (2, "view", "first_name", True, False),
        (2, "view", "last_name", True, False),
        (2, "view", "email", True, False),
        (2, "view", "unit", True, False),
    ]

    for subject_level, action, field_name, can_view, can_edit in default_field_rules:
        AccessFieldRule.objects.update_or_create(
            ruleset=ruleset,
            resource="user",
            action=action,
            subject_level=subject_level,
            field_name=field_name,
            priority=10,
            defaults={
                "can_view": can_view,
                "can_edit": can_edit,
                "is_active": True,
                "note": "Автозаполнение стартового набора",
            },
        )

    choice_rules = [
        (0, "create", "unit", "all"),
        (0, "update", "unit", "all"),
        (1, "create", "unit", "own_and_descendants"),
        (1, "update", "unit", "own_and_descendants"),
        (2, "create", "unit", "own_unit"),
        (2, "update", "unit", "own_unit"),
    ]

    for subject_level, action, field_name, scope in choice_rules:
        AccessChoiceRule.objects.update_or_create(
            ruleset=ruleset,
            resource="user",
            action=action,
            subject_level=subject_level,
            field_name=field_name,
            priority=10,
            defaults={
                "scope": scope,
                "is_active": True,
                "note": "Автозаполнение стартового набора",
            },
        )


def seed_default_person_rules(ruleset):
    default_rules = [
        (0, "view", True, "all", 10),
        (0, "create", True, "all", 10),
        (0, "update", True, "all", 10),
        (0, "delete", True, "all", 10),
        (0, "manage_exemptions", True, "all", 10),
        (0, "manage_clearances", True, "all", 10),

        (1, "view", True, "own_and_descendants", 10),
        (1, "create", True, "own_unit", 10),
        (1, "update", True, "own_and_descendants", 10),
        (1, "delete", False, "none", 10),
        (1, "manage_exemptions", True, "own_and_descendants", 10),
        (1, "manage_clearances", True, "own_and_descendants", 10),

        (2, "view", True, "own_unit", 10),
        (2, "create", True, "own_unit", 10),
        (2, "update", True, "own_unit", 10),
        (2, "delete", False, "none", 10),
        (2, "manage_exemptions", True, "own_unit", 10),
        (2, "manage_clearances", True, "own_unit", 10),
    ]

    for subject_level, action, is_allowed, scope, priority in default_rules:
        AccessRule.objects.update_or_create(
            ruleset=ruleset,
            resource="person",
            action=action,
            subject_level=subject_level,
            priority=priority,
            defaults={
                "is_allowed": is_allowed,
                "scope": scope,
                "is_active": True,
                "note": "Автозаполнение стартового набора",
            },
        )

    default_field_rules = [
        (0, "view", "last_name", True, False),
        (0, "view", "first_name", True, False),
        (0, "view", "middle_name", True, False),
        (0, "view", "rank", True, False),
        (0, "view", "unit", True, False),

        (0, "create", "last_name", True, True),
        (0, "create", "first_name", True, True),
        (0, "create", "middle_name", True, True),
        (0, "create", "rank", True, True),
        (0, "create", "unit", True, True),

        (0, "update", "last_name", True, True),
        (0, "update", "first_name", True, True),
        (0, "update", "middle_name", True, True),
        (0, "update", "rank", True, True),
        (0, "update", "unit", True, True),

        (1, "view", "last_name", True, False),
        (1, "view", "first_name", True, False),
        (1, "view", "middle_name", True, False),
        (1, "view", "rank", True, False),
        (1, "view", "unit", True, False),

        (1, "create", "last_name", True, True),
        (1, "create", "first_name", True, True),
        (1, "create", "middle_name", True, True),
        (1, "create", "rank", True, True),
        (1, "create", "unit", True, True),

        (1, "update", "last_name", True, True),
        (1, "update", "first_name", True, True),
        (1, "update", "middle_name", True, True),
        (1, "update", "rank", True, True),
        (1, "update", "unit", True, True),

        (2, "view", "last_name", True, False),
        (2, "view", "first_name", True, False),
        (2, "view", "middle_name", True, False),
        (2, "view", "rank", True, False),
        (2, "view", "unit", True, False),

        (2, "create", "last_name", True, True),
        (2, "create", "first_name", True, True),
        (2, "create", "middle_name", True, True),
        (2, "create", "rank", True, True),
        (2, "create", "unit", True, True),

        (2, "update", "last_name", True, True),
        (2, "update", "first_name", True, True),
        (2, "update", "middle_name", True, True),
        (2, "update", "rank", True, True),
        (2, "update", "unit", True, True),
    ]

    for subject_level, action, field_name, can_view, can_edit in default_field_rules:
        AccessFieldRule.objects.update_or_create(
            ruleset=ruleset,
            resource="person",
            action=action,
            subject_level=subject_level,
            field_name=field_name,
            priority=10,
            defaults={
                "can_view": can_view,
                "can_edit": can_edit,
                "is_active": True,
                "note": "Автозаполнение стартового набора",
            },
        )

    choice_rules = [
        (0, "create", "unit", "all"),
        (0, "update", "unit", "all"),
        (0, "manage_clearances", "duty_type", "all"),

        (1, "create", "unit", "own_and_descendants"),
        (1, "update", "unit", "own_and_descendants"),
        (1, "manage_clearances", "duty_type", "own_and_descendants"),

        (2, "create", "unit", "own_unit"),
        (2, "update", "unit", "own_unit"),
        (2, "manage_clearances", "duty_type", "own_unit"),
    ]

    for subject_level, action, field_name, scope in choice_rules:
        AccessChoiceRule.objects.update_or_create(
            ruleset=ruleset,
            resource="person",
            action=action,
            subject_level=subject_level,
            field_name=field_name,
            priority=10,
            defaults={
                "scope": scope,
                "is_active": True,
                "note": "Автозаполнение стартового набора",
            },
        )