from people.models import Person
from units.models import Unit
from duty_types.models import DutyType

from .base import BaseAccessService
from .legacy import LegacyAccessAdapter
from .scopes import filter_queryset_by_scope, matches_scope
from .unit_sets import get_scope_unit_ids


class PersonAccessService(BaseAccessService):
    PERSON_UNIT_LOOKUP = "unit_id"
    DUTY_TYPE_UNIT_LOOKUP = "created_by_unit_id"

    PERSON_VIEW_FIELDS_DEFAULT = {"last_name", "first_name", "middle_name", "rank", "unit"}
    PERSON_UPDATE_FIELDS_DEFAULT = {"last_name", "first_name", "middle_name", "rank", "unit"}
    PERSON_CREATE_FIELDS_DEFAULT = {"last_name", "first_name", "middle_name", "rank", "unit"}

    def __init__(self, ctx):
        super().__init__(ctx)
        self.legacy = LegacyAccessAdapter(ctx.user)

    def can(self, action: str, person: Person = None) -> bool:
        rule = self._get_rule("person", action)
        if rule:
            if not rule.is_allowed:
                return False
            if person is None:
                return True
            return matches_scope(self.ctx, getattr(person, "unit_id", None), rule.scope)

        return self.legacy.can_person(action, person)

    def scope_queryset(self, queryset):
        rule = self._get_rule("person", "view")
        if rule:
            if not rule.is_allowed:
                return queryset.none()
            return filter_queryset_by_scope(self.ctx, queryset, self.PERSON_UNIT_LOOKUP, rule.scope)

        return self.legacy.visible_people(queryset)

    def visible_fields(self, action: str) -> set[str]:
        if action == "create":
            default_fields = set(self.PERSON_CREATE_FIELDS_DEFAULT)
        elif action == "update":
            default_fields = set(self.PERSON_UPDATE_FIELDS_DEFAULT)
        else:
            default_fields = set(self.PERSON_VIEW_FIELDS_DEFAULT)

        rules = self._get_field_rules("person", action)
        if rules is None:
            return default_fields

        return {rule.field_name for rule in rules if rule.can_view}

    def editable_fields(self, action: str) -> set[str]:
        if action == "create":
            default_fields = set(self.PERSON_CREATE_FIELDS_DEFAULT)
        elif action == "update":
            default_fields = set(self.PERSON_UPDATE_FIELDS_DEFAULT)
        else:
            default_fields = set()

        rules = self._get_field_rules("person", action)
        if rules is None:
            return default_fields

        return {rule.field_name for rule in rules if rule.can_edit}

    def allowed_units_for_creation(self):
        return self._allowed_units_for_field("create", "unit")

    def allowed_units_for_update(self):
        return self._allowed_units_for_field("update", "unit")

    def allowed_duty_types_for_clearance(self):
        choice_rule = self._get_choice_rule("person", "manage_clearances", "duty_type")
        qs = DutyType.objects.select_related("unit", "created_by_unit").all()

        if choice_rule:
            allowed_unit_ids = self._resolve_choice_rule_unit_ids(choice_rule)
            if not allowed_unit_ids:
                return qs.none()
            return qs.filter(created_by_unit_id__in=list(allowed_unit_ids)).order_by("name")

        action_rule = self._get_rule("person", "manage_clearances")
        if action_rule and action_rule.is_allowed:
            return filter_queryset_by_scope(self.ctx, qs, self.DUTY_TYPE_UNIT_LOOKUP, action_rule.scope).order_by("name")

        return qs.none()

    def _allowed_units_for_field(self, action: str, field_name: str):
        choice_rule = self._get_choice_rule("person", action, field_name)
        qs = Unit.objects.select_related("unit_type", "parent").all()

        if choice_rule:
            if choice_rule.mode == "scope":
                return filter_queryset_by_scope(self.ctx, qs, "id", choice_rule.scope).order_by("name")

            allowed_unit_ids = self._resolve_choice_rule_unit_ids(choice_rule)
            if not allowed_unit_ids:
                return qs.none()

            return qs.filter(id__in=list(allowed_unit_ids)).order_by("name")

        action_rule = self._get_rule("person", action)
        if action_rule and action_rule.is_allowed:
            return filter_queryset_by_scope(self.ctx, qs, "id", action_rule.scope).order_by("name")

        return Unit.objects.filter(id=self.ctx.own_unit_id).order_by("name")

    def _resolve_choice_rule_unit_ids(self, choice_rule) -> set[int]:
        explicit_ids = set(choice_rule.units.values_list("id", flat=True))

        if choice_rule.mode == "specific_units":
            return explicit_ids

        if choice_rule.mode == "scope_plus_units":
            scope_ids = get_scope_unit_ids(self.ctx, choice_rule.scope)
            return scope_ids | explicit_ids

        return get_scope_unit_ids(self.ctx, choice_rule.scope)