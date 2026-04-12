from .assignment_access import AssignmentAccessService
from .context import AccessContext
from .duty_type_access import DutyTypeAccessService
from .person_access import PersonAccessService
from .plan_access import PlanAccessService
from .seed import (
    seed_default_assignment_rules,
    seed_default_duty_type_rules,
    seed_default_person_rules,
    seed_default_plan_rules,
    seed_default_unit_rules,
    seed_default_unit_type_rules,
    seed_default_user_rules,
)
from .unit_access import UnitAccessService
from .unit_type_access import UnitTypeAccessService
from .user_access import UserAccessService


class AccessManager:
    def __init__(self, user):
        self.user = user
        self.ctx = AccessContext(user)

        self.user_access = UserAccessService(self.ctx)
        self.person_access = PersonAccessService(self.ctx)
        self.unit_access = UnitAccessService(self.ctx)
        self.unit_type_access = UnitTypeAccessService(self.ctx)
        self.duty_type_access = DutyTypeAccessService(self.ctx)
        self.plan_access = PlanAccessService(self.ctx)
        self.assignment_access = AssignmentAccessService(self.ctx)

        self.ruleset = self.user_access.ruleset

    def can_user(self, action, target_user=None):
        return self.user_access.can(action, target_user)

    def scope_users(self, queryset):
        return self.user_access.scope_queryset(queryset)

    def visible_user_fields(self, action):
        return self.user_access.visible_fields(action)

    def editable_user_fields(self, action):
        return self.user_access.editable_fields(action)

    def allowed_units_for_user_creation(self):
        return self.user_access.allowed_units_for_creation()

    def allowed_units_for_user_update(self):
        return self.user_access.allowed_units_for_update()

    def can_person(self, action, person=None):
        return self.person_access.can(action, person)

    def scope_people(self, queryset):
        return self.person_access.scope_queryset(queryset)

    def visible_person_fields(self, action):
        return self.person_access.visible_fields(action)

    def editable_person_fields(self, action):
        return self.person_access.editable_fields(action)

    def allowed_units_for_person_creation(self):
        return self.person_access.allowed_units_for_creation()

    def allowed_units_for_person_update(self):
        return self.person_access.allowed_units_for_update()

    def allowed_duty_types_for_clearance(self):
        return self.person_access.allowed_duty_types_for_clearance()

    def can_unit(self, action, unit=None):
        return self.unit_access.can(action, unit)

    def scope_units_tree(self, queryset):
        return self.unit_access.scope_queryset(queryset)

    def visible_unit_fields(self, action):
        return self.unit_access.visible_fields(action)

    def editable_unit_fields(self, action):
        return self.unit_access.editable_fields(action)

    def allowed_parents_for_unit_creation(self):
        return self.unit_access.allowed_parents_for_creation()

    def allowed_parents_for_unit_update(self):
        return self.unit_access.allowed_parents_for_update()

    def allowed_unit_types_for_unit_creation(self):
        return self.unit_access.allowed_unit_types_for_creation()

    def allowed_unit_types_for_unit_update(self):
        return self.unit_access.allowed_unit_types_for_update()

    def can_unit_type(self, action, unit_type=None):
        return self.unit_type_access.can(action, unit_type)

    def scope_unit_types(self, queryset):
        return self.unit_type_access.scope_queryset(queryset)

    def visible_unit_type_fields(self, action):
        return self.unit_type_access.visible_fields(action)

    def editable_unit_type_fields(self, action):
        return self.unit_type_access.editable_fields(action)

    def can_duty_type(self, action, duty_type=None):
        return self.duty_type_access.can(action, duty_type)

    def scope_duty_types(self, queryset):
        return self.duty_type_access.scope_queryset(queryset)

    def visible_duty_type_fields(self, action):
        return self.duty_type_access.visible_fields(action)

    def editable_duty_type_fields(self, action):
        return self.duty_type_access.editable_fields(action)

    def allowed_units_for_duty_type_creation(self):
        return self.duty_type_access.allowed_units_for_creation()

    def allowed_units_for_duty_type_update(self):
        return self.duty_type_access.allowed_units_for_update()

    def can_plan(self, action, schedule=None):
        return self.plan_access.can(action, schedule)

    def scope_plans(self, queryset):
        return self.plan_access.scope_queryset(queryset)

    def visible_plan_fields(self, action):
        return self.plan_access.visible_fields(action)

    def editable_plan_fields(self, action):
        return self.plan_access.editable_fields(action)

    def allowed_delegate_units_for_plan_days(self, schedule):
        return self.plan_access.allowed_delegate_units_for_days(schedule)

    def can_assignment(self, action, plan=None):
        return self.assignment_access.can(action, plan)

    def seed_default_user_rules(self):
        seed_default_user_rules(self.ruleset)

    def seed_default_person_rules(self):
        seed_default_person_rules(self.ruleset)

    def seed_default_unit_rules(self):
        seed_default_unit_rules(self.ruleset)

    def seed_default_unit_type_rules(self):
        seed_default_unit_type_rules(self.ruleset)

    def seed_default_duty_type_rules(self):
        seed_default_duty_type_rules(self.ruleset)

    def seed_default_plan_rules(self):
        seed_default_plan_rules(self.ruleset)

    def seed_default_assignment_rules(self):
        seed_default_assignment_rules(self.ruleset)