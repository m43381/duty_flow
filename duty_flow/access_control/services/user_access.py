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
            target_unit_id = getattr(getattr(target_user, "profile", None), "unit_id", None)
            return matches_scope(self.ctx, target_unit_id, rule.scope)

        return self.legacy.can_user(action, target_user)

    def scope_queryset(self, queryset):
        rule = self._get_rule("user", "view")
        if rule:
            if not rule.is_allowed:
                return queryset.none()
            return filter_queryset_by_scope(self.ctx, queryset, self.USER_UNIT_LOOKUP, rule.scope)

        return self.legacy.visible_users(queryset)

    def visible_fields(self, action: str) -> set[str]:
        if action == "create":
            default_fields = set(self.USER_CREATE_FIELDS_DEFAULT)
        elif action == "update":
            default_fields = set(self.USER_UPDATE_FIELDS_DEFAULT)
        else:
            default_fields = set(self.USER_VIEW_FIELDS_DEFAULT)

        rules = self._get_field_rules("user", action)
        if rules is None:
            return default_fields

        return {rule.field_name for rule in rules if rule.can_view}

    def editable_fields(self, action: str) -> set[str]:
        if action == "create":
            default_fields = set(self.USER_CREATE_FIELDS_DEFAULT)
        elif action == "update":
            default_fields = set(self.USER_UPDATE_FIELDS_DEFAULT)
        else:
            default_fields = set()

        rules = self._get_field_rules("user", action)
        if rules is None:
            return default_fields

        return {rule.field_name for rule in rules if rule.can_edit}

    def allowed_units_for_creation(self):
        return self._allowed_units_for_field("create", "unit")

    def allowed_units_for_update(self):
        return self._allowed_units_for_field("update", "unit")

    def _allowed_units_for_field(self, action: str, field_name: str):
        choice_rule = self._get_choice_rule("user", action, field_name)
        qs = Unit.objects.select_related("unit_type", "parent").all()

        if choice_rule:
            if choice_rule.mode == "scope":
                return filter_queryset_by_scope(self.ctx, qs, "id", choice_rule.scope).order_by("name")

            explicit_ids = set(choice_rule.units.values_list("id", flat=True))

            if choice_rule.mode == "specific_units":
                return qs.filter(id__in=list(explicit_ids)).order_by("name")

            if choice_rule.mode == "scope_plus_units":
                scoped_ids = set(
                    filter_queryset_by_scope(self.ctx, Unit.objects.all(), "id", choice_rule.scope)
                    .values_list("id", flat=True)
                )
                return qs.filter(id__in=list(scoped_ids | explicit_ids)).order_by("name")

            if choice_rule.mode == "all_values":
                return qs.order_by("name")

        action_rule = self._get_rule("user", action)
        if action_rule and action_rule.is_allowed:
            return filter_queryset_by_scope(self.ctx, qs, "id", action_rule.scope).order_by("name")

        return Unit.objects.filter(id=self.ctx.own_unit_id).order_by("name")