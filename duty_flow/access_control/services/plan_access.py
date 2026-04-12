from duty_plans.models import MonthlySchedule
from units.models import Unit

from .base import BaseAccessService
from .scopes import filter_queryset_by_scope, matches_scope


class PlanAccessService(BaseAccessService):
    PLAN_UNIT_LOOKUP = "unit_id"

    PLAN_VIEW_FIELDS_DEFAULT = {"month", "name", "status"}
    PLAN_UPDATE_FIELDS_DEFAULT = {"month", "name", "status"}
    PLAN_CREATE_FIELDS_DEFAULT = {"month", "name", "status"}

    def can(self, action: str, schedule: MonthlySchedule = None) -> bool:
        rule = self._get_rule("plan", action)
        if rule:
            if not rule.is_allowed:
                return False
            if schedule is None:
                return True
            return matches_scope(self.ctx, getattr(schedule, "unit_id", None), rule.scope)

        return self._legacy_can(action, schedule)

    def scope_queryset(self, queryset):
        rule = self._get_rule("plan", "view")
        if rule:
            if not rule.is_allowed:
                return queryset.none()
            return filter_queryset_by_scope(self.ctx, queryset, self.PLAN_UNIT_LOOKUP, rule.scope)

        return self._legacy_visible_schedules(queryset)

    def visible_fields(self, action: str) -> set[str]:
        if action == "create":
            default_fields = set(self.PLAN_CREATE_FIELDS_DEFAULT)
        elif action == "update":
            default_fields = set(self.PLAN_UPDATE_FIELDS_DEFAULT)
        else:
            default_fields = set(self.PLAN_VIEW_FIELDS_DEFAULT)

        rules = self._get_field_rules("plan", action)
        if rules is None:
            return default_fields

        return {rule.field_name for rule in rules if rule.can_view}

    def editable_fields(self, action: str) -> set[str]:
        if action == "create":
            default_fields = set(self.PLAN_CREATE_FIELDS_DEFAULT)
        elif action == "update":
            default_fields = set(self.PLAN_UPDATE_FIELDS_DEFAULT)
        else:
            default_fields = set()

        rules = self._get_field_rules("plan", action)
        if rules is None:
            return default_fields

        return {rule.field_name for rule in rules if rule.can_edit}

    def allowed_delegate_units_for_days(self, schedule: MonthlySchedule):
        choice_rule = self._get_choice_rule("plan", "manage_days", "delegate_unit")
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

        action_rule = self._get_rule("plan", "manage_days")
        if action_rule and action_rule.is_allowed:
            return filter_queryset_by_scope(self.ctx, qs, "id", action_rule.scope).order_by("name")

        return Unit.objects.none()

    def _legacy_can(self, action: str, schedule: MonthlySchedule = None) -> bool:
        if action in {"create", "accept_incoming"}:
            return True

        if schedule is None:
            return True

        return getattr(schedule, "unit_id", None) == self.ctx.own_unit_id

    def _legacy_visible_schedules(self, queryset):
        if self.ctx.own_unit_id is None:
            return queryset.none()
        return queryset.filter(unit_id=self.ctx.own_unit_id)