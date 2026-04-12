from duty_types.models import DutyType
from units.models import Unit

from .base import BaseAccessService
from .scopes import filter_queryset_by_scope, matches_scope


class DutyTypeAccessService(BaseAccessService):
    DUTY_TYPE_UNIT_LOOKUP = "created_by_unit_id"

    DUTY_TYPE_VIEW_FIELDS_DEFAULT = {"name", "description", "required_people", "unit"}
    DUTY_TYPE_UPDATE_FIELDS_DEFAULT = {"name", "description", "required_people", "unit"}
    DUTY_TYPE_CREATE_FIELDS_DEFAULT = {"name", "description", "required_people", "unit"}

    def can(self, action: str, duty_type: DutyType = None) -> bool:
        rule = self._get_rule("duty_type", action)
        if rule:
            if not rule.is_allowed:
                return False
            if duty_type is None:
                return True
            return matches_scope(self.ctx, getattr(duty_type, "created_by_unit_id", None), rule.scope)

        return self._legacy_can(action, duty_type)

    def scope_queryset(self, queryset):
        rule = self._get_rule("duty_type", "view")
        if rule:
            if not rule.is_allowed:
                return queryset.none()
            return filter_queryset_by_scope(self.ctx, queryset, self.DUTY_TYPE_UNIT_LOOKUP, rule.scope)

        return self._legacy_visible_duty_types()

    def visible_fields(self, action: str) -> set[str]:
        if action == "create":
            default_fields = set(self.DUTY_TYPE_CREATE_FIELDS_DEFAULT)
        elif action == "update":
            default_fields = set(self.DUTY_TYPE_UPDATE_FIELDS_DEFAULT)
        else:
            default_fields = set(self.DUTY_TYPE_VIEW_FIELDS_DEFAULT)

        rules = self._get_field_rules("duty_type", action)
        if rules is None:
            return default_fields

        return {rule.field_name for rule in rules if rule.can_view}

    def editable_fields(self, action: str) -> set[str]:
        if action == "create":
            default_fields = set(self.DUTY_TYPE_CREATE_FIELDS_DEFAULT)
        elif action == "update":
            default_fields = set(self.DUTY_TYPE_UPDATE_FIELDS_DEFAULT)
        else:
            default_fields = set()

        rules = self._get_field_rules("duty_type", action)
        if rules is None:
            return default_fields

        return {rule.field_name for rule in rules if rule.can_edit}

    def allowed_units_for_creation(self):
        return self._allowed_units_for_field("create", "unit")

    def allowed_units_for_update(self):
        return self._allowed_units_for_field("update", "unit")

    def _allowed_units_for_field(self, action: str, field_name: str):
        choice_rule = self._get_choice_rule("duty_type", action, field_name)
        qs = Unit.objects.select_related("parent", "unit_type").all()

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

        action_rule = self._get_rule("duty_type", action)
        if action_rule and action_rule.is_allowed:
            return filter_queryset_by_scope(self.ctx, qs, "id", action_rule.scope).order_by("name")

        return qs.none()

    def _legacy(self):
        from core.services.duty_type_service import DutyTypeService
        return DutyTypeService

    def _legacy_can(self, action: str, duty_type: DutyType = None) -> bool:
        svc = self._legacy()

        if action == "view":
            if duty_type is None:
                return True
            return svc.can_edit(self.ctx.user, duty_type)

        if action == "create":
            return True

        if action in {"update", "delete"} and duty_type is not None:
            return svc.can_edit(self.ctx.user, duty_type)

        return False

    def _legacy_visible_duty_types(self):
        return self._legacy().get_user_duty_types(self.ctx.user)