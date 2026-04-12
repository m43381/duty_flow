from duty_plans.models import DayPlan

from .base import BaseAccessService
from .scopes import matches_scope


class AssignmentAccessService(BaseAccessService):
    def can(self, action: str, plan: DayPlan = None) -> bool:
        rule = self._get_rule("assignment", action)
        if rule:
            if not rule.is_allowed:
                return False
            if plan is None:
                return True
            return matches_scope(self.ctx, getattr(plan, "unit_id", None), rule.scope)

        return self._legacy_can(action, plan)

    def _legacy_can(self, action: str, plan: DayPlan = None) -> bool:
        if action == "view":
            return True

        if plan is None:
            return True

        return getattr(plan, "unit_id", None) == self.ctx.own_unit_id