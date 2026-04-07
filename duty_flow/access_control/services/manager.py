from .context import AccessContext
from .person_access import PersonAccessService
from .seed import seed_default_person_rules, seed_default_user_rules
from .user_access import UserAccessService


class AccessManager:
    def __init__(self, user):
        self.user = user
        self.ctx = AccessContext(user)

        self.user_access = UserAccessService(self.ctx)
        self.person_access = PersonAccessService(self.ctx)

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

    def seed_default_user_rules(self):
        seed_default_user_rules(self.ruleset)

    def seed_default_person_rules(self):
        seed_default_person_rules(self.ruleset)