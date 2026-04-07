from people.models import Person
from units.models import Unit

from .base import BaseAccessService
from .legacy import LegacyAccessAdapter
from .scopes import filter_queryset_by_scope, matches_scope


class PersonAccessService(BaseAccessService):
    PERSON_UNIT_LOOKUP = "unit_id"

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

    def _allowed_units_for_field(self, action: str, field_name: str):
        choice_rule = self._get_choice_rule("person", action, field_name)
        qs = Unit.objects.select_related("unit_type", "parent").all()

        if choice_rule:
            return filter_queryset_by_scope(self.ctx, qs, "id", choice_rule.scope).order_by("name")

        action_rule = self._get_rule("person", action)
        if action_rule and action_rule.is_allowed:
            return filter_queryset_by_scope(self.ctx, qs, "id", action_rule.scope).order_by("name")

        return Unit.objects.filter(id=self.ctx.own_unit_id).order_by("name")