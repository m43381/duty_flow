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


def seed_default_unit_rules(ruleset):
    default_rules = [
        (0, "view", True, "all", 10),
        (0, "create", True, "all", 10),
        (0, "update", True, "all", 10),
        (0, "delete", True, "all", 10),

        (1, "view", True, "own_and_descendants", 10),
        (1, "create", True, "own_and_descendants", 10),
        (1, "update", True, "own_and_descendants", 10),
        (1, "delete", False, "none", 10),

        (2, "view", True, "own_unit", 10),
        (2, "create", False, "none", 10),
        (2, "update", False, "none", 10),
        (2, "delete", False, "none", 10),
    ]

    for subject_level, action, is_allowed, scope, priority in default_rules:
        AccessRule.objects.update_or_create(
            ruleset=ruleset,
            resource="unit",
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
        (0, "view", "name", True, False),
        (0, "view", "parent", True, False),
        (0, "view", "unit_type", True, False),

        (0, "create", "name", True, True),
        (0, "create", "parent", True, True),
        (0, "create", "unit_type", True, True),

        (0, "update", "name", True, True),
        (0, "update", "parent", True, True),
        (0, "update", "unit_type", True, True),

        (1, "view", "name", True, False),
        (1, "view", "parent", True, False),
        (1, "view", "unit_type", True, False),

        (1, "create", "name", True, True),
        (1, "create", "parent", True, True),
        (1, "create", "unit_type", True, True),

        (1, "update", "name", True, True),
        (1, "update", "parent", True, True),
        (1, "update", "unit_type", True, True),

        (2, "view", "name", True, False),
        (2, "view", "parent", True, False),
        (2, "view", "unit_type", True, False),
    ]

    for subject_level, action, field_name, can_view, can_edit in default_field_rules:
        AccessFieldRule.objects.update_or_create(
            ruleset=ruleset,
            resource="unit",
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

    parent_choice_rules = [
        (0, "create", "parent", "scope", "all"),
        (0, "update", "parent", "scope", "all"),

        (1, "create", "parent", "scope", "own_and_descendants"),
        (1, "update", "parent", "scope", "own_and_descendants"),

        (2, "create", "parent", "scope", "none"),
        (2, "update", "parent", "scope", "none"),
    ]

    for subject_level, action, field_name, mode, scope in parent_choice_rules:
        AccessChoiceRule.objects.update_or_create(
            ruleset=ruleset,
            resource="unit",
            action=action,
            subject_level=subject_level,
            field_name=field_name,
            priority=10,
            defaults={
                "mode": mode,
                "scope": scope,
                "is_active": True,
                "note": "Автозаполнение стартового набора",
            },
        )

    unit_type_choice_rules = [
        (0, "create", "unit_type", "all_values"),
        (0, "update", "unit_type", "all_values"),
        (1, "create", "unit_type", "all_values"),
        (1, "update", "unit_type", "all_values"),
        (2, "create", "unit_type", "specific_unit_types"),
        (2, "update", "unit_type", "specific_unit_types"),
    ]

    for subject_level, action, field_name, mode in unit_type_choice_rules:
        choice_rule, _ = AccessChoiceRule.objects.update_or_create(
            ruleset=ruleset,
            resource="unit",
            action=action,
            subject_level=subject_level,
            field_name=field_name,
            priority=10,
            defaults={
                "mode": mode,
                "scope": "none",
                "is_active": True,
                "note": "Автозаполнение стартового набора",
            },
        )

        if mode == "all_values":
            choice_rule.unit_types.set(AccessChoiceRule._meta.get_field("unit_types").related_model.objects.all())