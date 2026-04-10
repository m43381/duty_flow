from access_control.models import AccessChoiceRule, AccessFieldRule, AccessRule
from units.models import Unit, UnitType


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
            defaults={"is_allowed": is_allowed, "scope": scope, "is_active": True, "note": "Автозаполнение стартового набора"},
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
            defaults={"is_allowed": is_allowed, "scope": scope, "is_active": True, "note": "Автозаполнение стартового набора"},
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
            defaults={"is_allowed": is_allowed, "scope": scope, "is_active": True, "note": "Автозаполнение стартового набора"},
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
            defaults={"mode": mode, "scope": scope, "is_active": True, "note": "Автозаполнение стартового набора"},
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
            defaults={"mode": mode, "scope": "none", "is_active": True, "note": "Автозаполнение стартового набора"},
        )
        if mode == "all_values":
            choice_rule.unit_types.set(UnitType.objects.all())


def seed_default_unit_type_rules(ruleset):
    default_rules = [
        (0, "view", True, "all", 10),
        (0, "create", True, "all", 10),
        (0, "update", True, "all", 10),
        (0, "delete", True, "all", 10),
        (1, "view", False, "none", 10),
        (1, "create", False, "none", 10),
        (1, "update", False, "none", 10),
        (1, "delete", False, "none", 10),
        (2, "view", False, "none", 10),
        (2, "create", False, "none", 10),
        (2, "update", False, "none", 10),
        (2, "delete", False, "none", 10),
    ]
    for subject_level, action, is_allowed, scope, priority in default_rules:
        AccessRule.objects.update_or_create(
            ruleset=ruleset,
            resource="unit_type",
            action=action,
            subject_level=subject_level,
            priority=priority,
            defaults={"is_allowed": is_allowed, "scope": scope, "is_active": True, "note": "Автозаполнение стартового набора"},
        )


def seed_default_duty_type_rules(ruleset):
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
            resource="duty_type",
            action=action,
            subject_level=subject_level,
            priority=priority,
            defaults={"is_allowed": is_allowed, "scope": scope, "is_active": True, "note": "Автозаполнение стартового набора"},
        )

    unit_choice_rules = [
        (0, "create", "unit", "all_values", "all"),
        (0, "update", "unit", "all_values", "all"),
        (1, "create", "unit", "scope", "own_and_descendants"),
        (1, "update", "unit", "scope", "own_and_descendants"),
        (2, "create", "unit", "scope", "none"),
        (2, "update", "unit", "scope", "none"),
    ]
    for subject_level, action, field_name, mode, scope in unit_choice_rules:
        choice_rule, _ = AccessChoiceRule.objects.update_or_create(
            ruleset=ruleset,
            resource="duty_type",
            action=action,
            subject_level=subject_level,
            field_name=field_name,
            priority=10,
            defaults={"mode": mode, "scope": scope, "is_active": True, "note": "Автозаполнение стартового набора"},
        )
        if mode == "all_values":
            choice_rule.units.set(Unit.objects.all())


def seed_default_plan_rules(ruleset):
    default_rules = [
        (0, "view", True, "all", 10),
        (0, "create", True, "all", 10),
        (0, "update", True, "all", 10),
        (0, "delete", True, "all", 10),
        (0, "manage_days", True, "all", 10),
        (0, "accept_incoming", True, "all", 10),

        (1, "view", True, "own_unit", 10),
        (1, "create", True, "own_unit", 10),
        (1, "update", True, "own_unit", 10),
        (1, "delete", True, "own_unit", 10),
        (1, "manage_days", True, "own_unit", 10),
        (1, "accept_incoming", True, "own_unit", 10),

        (2, "view", True, "own_unit", 10),
        (2, "create", True, "own_unit", 10),
        (2, "update", True, "own_unit", 10),
        (2, "delete", False, "none", 10),
        (2, "manage_days", True, "own_unit", 10),
        (2, "accept_incoming", True, "own_unit", 10),
    ]
    for subject_level, action, is_allowed, scope, priority in default_rules:
        AccessRule.objects.update_or_create(
            ruleset=ruleset,
            resource="plan",
            action=action,
            subject_level=subject_level,
            priority=priority,
            defaults={"is_allowed": is_allowed, "scope": scope, "is_active": True, "note": "Автозаполнение стартового набора"},
        )

    field_rules = [
        (0, "view", "month", True, False),
        (0, "view", "name", True, False),
        (0, "view", "status", True, False),
        (0, "create", "month", True, True),
        (0, "create", "name", True, True),
        (0, "create", "status", True, True),
        (0, "update", "month", True, True),
        (0, "update", "name", True, True),
        (0, "update", "status", True, True),

        (1, "view", "month", True, False),
        (1, "view", "name", True, False),
        (1, "view", "status", True, False),
        (1, "create", "month", True, True),
        (1, "create", "name", True, True),
        (1, "create", "status", True, True),
        (1, "update", "month", True, True),
        (1, "update", "name", True, True),
        (1, "update", "status", True, True),

        (2, "view", "month", True, False),
        (2, "view", "name", True, False),
        (2, "view", "status", True, False),
        (2, "create", "month", True, True),
        (2, "create", "name", True, True),
        (2, "create", "status", True, True),
        (2, "update", "month", True, True),
        (2, "update", "name", True, True),
        (2, "update", "status", True, True),
    ]
    for subject_level, action, field_name, can_view, can_edit in field_rules:
        AccessFieldRule.objects.update_or_create(
            ruleset=ruleset,
            resource="plan",
            action=action,
            subject_level=subject_level,
            field_name=field_name,
            priority=10,
            defaults={"can_view": can_view, "can_edit": can_edit, "is_active": True, "note": "Автозаполнение стартового набора"},
        )

    delegate_choice_rules = [
        (0, "manage_days", "delegate_unit", "all_values", "all"),
        (1, "manage_days", "delegate_unit", "specific_units", "none"),
        (2, "manage_days", "delegate_unit", "specific_units", "none"),
    ]
    for subject_level, action, field_name, mode, scope in delegate_choice_rules:
        choice_rule, _ = AccessChoiceRule.objects.update_or_create(
            ruleset=ruleset,
            resource="plan",
            action=action,
            subject_level=subject_level,
            field_name=field_name,
            priority=10,
            defaults={"mode": mode, "scope": scope, "is_active": True, "note": "Автозаполнение стартового набора"},
        )
        if mode == "all_values":
            choice_rule.units.set(Unit.objects.all())