from units.models import UnitType

from .base import BaseAccessService


class UnitTypeAccessService(BaseAccessService):
    UNIT_TYPE_VIEW_FIELDS_DEFAULT = {"name", "level"}
    UNIT_TYPE_UPDATE_FIELDS_DEFAULT = {"name", "level"}
    UNIT_TYPE_CREATE_FIELDS_DEFAULT = {"name", "level"}

    def can(self, action: str, unit_type: UnitType = None) -> bool:
        rule = self._get_rule("unit_type", action)
        if rule:
            return rule.is_allowed

        # legacy fallback: только уровень 0
        return self.ctx.user_level == 0

    def scope_queryset(self, queryset):
        rule = self._get_rule("unit_type", "view")
        if rule:
            return queryset if rule.is_allowed else queryset.none()

        return queryset if self.ctx.user_level == 0 else queryset.none()

    def visible_fields(self, action: str) -> set[str]:
        if action == "create":
            default_fields = set(self.UNIT_TYPE_CREATE_FIELDS_DEFAULT)
        elif action == "update":
            default_fields = set(self.UNIT_TYPE_UPDATE_FIELDS_DEFAULT)
        else:
            default_fields = set(self.UNIT_TYPE_VIEW_FIELDS_DEFAULT)

        rules = self._get_field_rules("unit_type", action)
        if rules is None:
            return default_fields

        return {rule.field_name for rule in rules if rule.can_view}

    def editable_fields(self, action: str) -> set[str]:
        if action == "create":
            default_fields = set(self.UNIT_TYPE_CREATE_FIELDS_DEFAULT)
        elif action == "update":
            default_fields = set(self.UNIT_TYPE_UPDATE_FIELDS_DEFAULT)
        else:
            default_fields = set()

        rules = self._get_field_rules("unit_type", action)
        if rules is None:
            return default_fields

        return {rule.field_name for rule in rules if rule.can_edit}