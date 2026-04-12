from units.models import Unit, UnitType

from .base import BaseAccessService
from .scopes import filter_queryset_by_scope, matches_scope


class UnitAccessService(BaseAccessService):
    UNIT_VIEW_FIELDS_DEFAULT = {"name", "parent", "unit_type"}
    UNIT_UPDATE_FIELDS_DEFAULT = {"name", "parent", "unit_type"}
    UNIT_CREATE_FIELDS_DEFAULT = {"name", "parent", "unit_type"}

    def can(self, action: str, unit: Unit = None) -> bool:
        rule = self._get_rule("unit", action)
        if rule:
            if not rule.is_allowed:
                return False
            if unit is None:
                return True
            return matches_scope(self.ctx, unit.id, rule.scope)

        return self._legacy_can(action, unit)

    def scope_queryset(self, queryset):
        rule = self._get_rule("unit", "view")
        if rule:
            if not rule.is_allowed:
                return queryset.none()

            if rule.scope == "all":
                return queryset

            allowed_ids = self._allowed_unit_ids_by_scope(rule.scope)
            return queryset.filter(id__in=list(allowed_ids))

        return self._legacy_visible_units()

    def visible_fields(self, action: str) -> set[str]:
        if action == "create":
            default_fields = set(self.UNIT_CREATE_FIELDS_DEFAULT)
        elif action == "update":
            default_fields = set(self.UNIT_UPDATE_FIELDS_DEFAULT)
        else:
            default_fields = set(self.UNIT_VIEW_FIELDS_DEFAULT)

        rules = self._get_field_rules("unit", action)
        if rules is None:
            return default_fields

        return {rule.field_name for rule in rules if rule.can_view}

    def editable_fields(self, action: str) -> set[str]:
        if action == "create":
            default_fields = set(self.UNIT_CREATE_FIELDS_DEFAULT)
        elif action == "update":
            default_fields = set(self.UNIT_UPDATE_FIELDS_DEFAULT)
        else:
            default_fields = set()

        rules = self._get_field_rules("unit", action)
        if rules is None:
            return default_fields

        return {rule.field_name for rule in rules if rule.can_edit}

    def allowed_parents_for_creation(self):
        return self._allowed_units_for_field("create", "parent")

    def allowed_parents_for_update(self):
        return self._allowed_units_for_field("update", "parent")

    def allowed_unit_types_for_creation(self):
        return self._allowed_unit_types_for_field("create", "unit_type")

    def allowed_unit_types_for_update(self):
        return self._allowed_unit_types_for_field("update", "unit_type")

    def _allowed_units_for_field(self, action: str, field_name: str):
        choice_rule = self._get_choice_rule("unit", action, field_name)
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

        action_rule = self._get_rule("unit", action)
        if action_rule and action_rule.is_allowed:
            return filter_queryset_by_scope(self.ctx, qs, "id", action_rule.scope).order_by("name")

        return qs.none()

    def _allowed_unit_types_for_field(self, action: str, field_name: str):
        choice_rule = self._get_choice_rule("unit", action, field_name)
        qs = UnitType.objects.all().order_by("level", "name")

        if choice_rule:
            if choice_rule.mode == "all_values":
                return qs

            if choice_rule.mode == "specific_unit_types":
                explicit_ids = set(choice_rule.unit_types.values_list("id", flat=True))
                return qs.filter(id__in=list(explicit_ids))

        action_rule = self._get_rule("unit", action)
        if action_rule and action_rule.is_allowed:
            return qs

        if self.ctx.user_level == 0:
            return qs

        return qs.none()

    def _allowed_unit_ids_by_scope(self, scope: str):
        if scope == "all":
            return set(Unit.objects.values_list("id", flat=True))
        if scope == "none":
            return set()
        if scope == "own_unit":
            return {self.ctx.own_unit_id} if self.ctx.own_unit_id else set()
        if scope == "descendants":
            return set(self.ctx.descendant_unit_ids)
        if scope == "own_and_descendants":
            ids = set(self.ctx.descendant_unit_ids)
            if self.ctx.own_unit_id:
                ids.add(self.ctx.own_unit_id)
            return ids
        return set()

    def _legacy(self):
        from users_app.access_service import AccessService
        return AccessService(self.ctx.user)

    def _legacy_can(self, action: str, unit: Unit = None) -> bool:
        access = self._legacy()

        if action == "view":
            if unit is None:
                return True
            return access.get_visible_units().filter(id=unit.id).exists()

        if action == "create":
            return access.get_available_parents_for_creation().exists()

        if action == "update" and unit is not None:
            return access.can_edit_unit(unit)

        if action == "delete" and unit is not None:
            return access.can_delete_unit(unit)

        return False

    def _legacy_visible_units(self):
        return self._legacy().get_visible_units()