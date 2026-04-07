from django.contrib.auth.models import User

from units.models import Unit
from .base import BaseAccessService
from .legacy import LegacyAccessAdapter
from .scopes import filter_queryset_by_scope, matches_scope


class UserAccessService(BaseAccessService):
    USER_UNIT_LOOKUP = "profile__unit_id"

    USER_VIEW_FIELDS_DEFAULT = {"username", "first_name", "last_name", "email", "unit"}
    USER_UPDATE_FIELDS_DEFAULT = {"username", "first_name", "last_name", "email"}
    USER_CREATE_FIELDS_DEFAULT = {"username", "first_name", "last_name", "email", "unit"}

    SYSTEM_ALWAYS_VISIBLE = {"password", "password_confirm"}
    SYSTEM_ALWAYS_EDITABLE = {"password", "password_confirm"}

    def __init__(self, ctx):
        super().__init__(ctx)
        self.legacy = LegacyAccessAdapter(ctx.user)

    def can(self, action: str, target_user: User = None) -> bool:
        rule = self._get_rule("user", action)
        if rule:
            if not rule.is_allowed:
                return False
            if target_user is None:
                return True
            unit_id = self._get_user_unit_id(target_user)
            return matches_scope(self.ctx, unit_id, rule.scope)

        return self.legacy.can_user(action, target_user)

    def scope_queryset(self, queryset):
        rule = self._get_rule("user", "view")
        if rule:
            if not rule.is_allowed:
                return queryset.none()
            return filter_queryset_by_scope(self.ctx, queryset, self.USER_UNIT_LOOKUP, rule.scope)

        return self.legacy.visible_users()

    def visible_fields(self, action: str) -> set[str]:
        if action == "create":
            default_fields = set(self.USER_CREATE_FIELDS_DEFAULT)
        elif action == "update":
            default_fields = set(self.USER_UPDATE_FIELDS_DEFAULT)
        else:
            default_fields = set(self.USER_VIEW_FIELDS_DEFAULT)

        rules = self._get_field_rules("user", action)
        if rules is None:
            if action == "create":
                default_fields.update(self.SYSTEM_ALWAYS_VISIBLE)
            return default_fields

        result = {rule.field_name for rule in rules if rule.can_view}
        if action == "create":
            result.update(self.SYSTEM_ALWAYS_VISIBLE)
        return result

    def editable_fields(self, action: str) -> set[str]:
        if action == "create":
            default_fields = set(self.USER_CREATE_FIELDS_DEFAULT)
        elif action == "update":
            default_fields = set(self.USER_UPDATE_FIELDS_DEFAULT)
        else:
            default_fields = set()

        rules = self._get_field_rules("user", action)
        if rules is None:
            if action == "create":
                default_fields.update(self.SYSTEM_ALWAYS_EDITABLE)
            return default_fields

        result = {rule.field_name for rule in rules if rule.can_edit}
        if action == "create":
            result.update(self.SYSTEM_ALWAYS_EDITABLE)
        return result

    def allowed_units_for_creation(self):
        return self._allowed_units_for_field("create", "unit")

    def allowed_units_for_update(self):
        return self._allowed_units_for_field("update", "unit")

    def _allowed_units_for_field(self, action: str, field_name: str):
        choice_rule = self._get_choice_rule("user", action, field_name)
        qs = Unit.objects.select_related("unit_type", "parent").all()

        if choice_rule:
            return filter_queryset_by_scope(self.ctx, qs, "id", choice_rule.scope).order_by("name")

        action_rule = self._get_rule("user", action)
        if action_rule and action_rule.is_allowed:
            return filter_queryset_by_scope(self.ctx, qs, "id", action_rule.scope).order_by("name")

        return self.legacy.available_creation_units()

    @staticmethod
    def _get_user_unit_id(user_obj):
        profile = getattr(user_obj, "profile", None)
        return getattr(profile, "unit_id", None) if profile else None