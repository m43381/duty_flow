from dataclasses import dataclass
from typing import Optional, Set

from django.contrib.auth.models import User
from django.db.models import QuerySet

from units.models import Unit
from .models import AccessFieldRule, AccessRule, AccessRuleSet


@dataclass
class AccessContext:
    user: User
    user_unit: Optional[Unit] = None
    user_level: Optional[int] = None
    descendant_unit_ids: Set[int] = None

    def __post_init__(self):
        self.descendant_unit_ids = set()

        profile = getattr(self.user, "profile", None)
        if not profile:
            return

        self.user_unit = profile.unit
        self.user_level = profile.level

        if self.user_unit:
            self.descendant_unit_ids = set(self.user_unit.get_descendants_ids())

    @property
    def own_unit_id(self):
        return self.user_unit.id if self.user_unit else None

    def matches_scope(self, unit_id: Optional[int], scope: str) -> bool:
        if scope == "all":
            return True
        if not unit_id:
            return False
        if scope == "none":
            return False
        if scope == "own_unit":
            return unit_id == self.own_unit_id
        if scope == "descendants":
            return unit_id in self.descendant_unit_ids
        if scope == "own_and_descendants":
            return unit_id == self.own_unit_id or unit_id in self.descendant_unit_ids
        return False

    def filter_queryset_by_scope(self, queryset: QuerySet, unit_lookup: str, scope: str) -> QuerySet:
        if scope == "all":
            return queryset
        if scope == "none":
            return queryset.none()

        if scope == "own_unit":
            if not self.own_unit_id:
                return queryset.none()
            return queryset.filter(**{unit_lookup: self.own_unit_id})

        if scope == "descendants":
            if not self.descendant_unit_ids:
                return queryset.none()
            return queryset.filter(**{f"{unit_lookup}__in": list(self.descendant_unit_ids)})

        if scope == "own_and_descendants":
            allowed_ids = set(self.descendant_unit_ids)
            if self.own_unit_id:
                allowed_ids.add(self.own_unit_id)
            if not allowed_ids:
                return queryset.none()
            return queryset.filter(**{f"{unit_lookup}__in": list(allowed_ids)})

        return queryset.none()


class AccessManager:
    USER_UNIT_LOOKUP = "profile__unit_id"

    USER_VIEW_FIELDS_DEFAULT = {"username", "first_name", "last_name", "email", "unit"}
    USER_UPDATE_FIELDS_DEFAULT = {"username", "first_name", "last_name", "email", "unit"}
    USER_CREATE_FIELDS_DEFAULT = {"username", "first_name", "last_name", "email", "unit"}

    SYSTEM_ALWAYS_VISIBLE = {"password1", "password2"}
    SYSTEM_ALWAYS_EDITABLE = {"password1", "password2"}

    def __init__(self, user: User):
        self.user = user
        self.ctx = AccessContext(user)
        self.ruleset = self._get_or_create_default_ruleset()

    def can_user(self, action: str, target_user: Optional[User] = None) -> bool:
        rule = self._get_rule("user", action)
        if rule:
            if not rule.is_allowed:
                return False
            if target_user is None:
                return True
            unit_id = self._get_user_unit_id(target_user)
            return self.ctx.matches_scope(unit_id, rule.scope)

        return self._legacy_can_user(action, target_user)

    def scope_users(self, queryset: QuerySet) -> QuerySet:
        rule = self._get_rule("user", "view")
        if rule:
            if not rule.is_allowed:
                return queryset.none()
            return self.ctx.filter_queryset_by_scope(queryset, self.USER_UNIT_LOOKUP, rule.scope)

        return self._legacy_visible_users()

    def visible_user_fields(self, action: str) -> set[str]:
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

    def editable_user_fields(self, action: str) -> set[str]:
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

    def allowed_units_for_user_creation(self):
        rule = self._get_rule("user", "create")
        qs = Unit.objects.select_related("unit_type", "parent").all()
        if rule and rule.is_allowed:
            return self.ctx.filter_queryset_by_scope(qs, "id", rule.scope).order_by("name")
        return self._legacy_available_creation_units()

    def allowed_units_for_user_update(self):
        rule = self._get_rule("user", "update")
        qs = Unit.objects.select_related("unit_type", "parent").all()
        if rule and rule.is_allowed:
            return self.ctx.filter_queryset_by_scope(qs, "id", rule.scope).order_by("name")
        return self._legacy_available_creation_units()

    def seed_default_user_rules(self):
        ruleset = self.ruleset

        default_rules = [
            (0, "view", True, "all", 10),
            (0, "create", True, "all", 10),
            (0, "update", True, "all", 10),
            (0, "delete", True, "all", 10),
            (0, "change_password", True, "all", 10),

            (1, "view", True, "own_and_descendants", 10),
            (1, "create", True, "own_and_descendants", 10),
            (1, "update", True, "own_and_descendants", 10),
            (1, "delete", False, "none", 10),
            (1, "change_password", True, "own_and_descendants", 10),

            (2, "view", True, "own_unit", 10),
            (2, "create", False, "none", 10),
            (2, "update", False, "none", 10),
            (2, "delete", False, "none", 10),
            (2, "change_password", False, "none", 10),
        ]

        for subject_level, action, is_allowed, scope, priority in default_rules:
            AccessRule.objects.update_or_create(
                ruleset=ruleset,
                resource="user",
                action=action,
                subject_level=subject_level,
                priority=priority,
                defaults={
                    "is_allowed": is_allowed,
                    "scope": scope,
                    "is_active": True,
                    "note": "Автозаполнение стартового набора",
                },
            )

        default_field_rules = [
            (0, "view", "username", True, False),
            (0, "view", "first_name", True, False),
            (0, "view", "last_name", True, False),
            (0, "view", "email", True, False),
            (0, "view", "unit", True, False),

            (0, "create", "username", True, True),
            (0, "create", "first_name", True, True),
            (0, "create", "last_name", True, True),
            (0, "create", "email", True, True),
            (0, "create", "unit", True, True),

            (0, "update", "username", True, True),
            (0, "update", "first_name", True, True),
            (0, "update", "last_name", True, True),
            (0, "update", "email", True, True),
            (0, "update", "unit", True, True),

            (1, "view", "username", True, False),
            (1, "view", "first_name", True, False),
            (1, "view", "last_name", True, False),
            (1, "view", "email", True, False),
            (1, "view", "unit", True, False),

            (1, "create", "username", True, True),
            (1, "create", "first_name", True, True),
            (1, "create", "last_name", True, True),
            (1, "create", "email", True, True),
            (1, "create", "unit", True, True),

            (1, "update", "username", True, True),
            (1, "update", "first_name", True, True),
            (1, "update", "last_name", True, True),
            (1, "update", "email", True, True),
            (1, "update", "unit", True, True),

            (2, "view", "username", True, False),
            (2, "view", "first_name", True, False),
            (2, "view", "last_name", True, False),
            (2, "view", "email", True, False),
            (2, "view", "unit", True, False),
        ]

        for subject_level, action, field_name, can_view, can_edit in default_field_rules:
            AccessFieldRule.objects.update_or_create(
                ruleset=ruleset,
                resource="user",
                action=action,
                subject_level=subject_level,
                field_name=field_name,
                priority=10,
                defaults={
                    "can_view": can_view,
                    "can_edit": can_edit,
                    "is_active": True,
                    "note": "Автозаполнение стартового набора",
                },
            )

    def _get_or_create_default_ruleset(self):
        ruleset = AccessRuleSet.get_default()
        if ruleset:
            return ruleset

        return AccessRuleSet.objects.create(
            name="Базовый набор",
            code="default",
            description="Основной активный набор правил доступа",
            is_active=True,
            is_default=True,
        )

    def _get_rule(self, resource: str, action: str):
        if self.ruleset is None or self.ctx.user_level is None:
            return None

        return (
            AccessRule.objects.filter(
                ruleset=self.ruleset,
                resource=resource,
                action=action,
                subject_level=self.ctx.user_level,
                is_active=True,
            )
            .order_by("priority", "id")
            .first()
        )

    def _get_field_rules(self, resource: str, action: str):
        if self.ruleset is None or self.ctx.user_level is None:
            return None

        qs = (
            AccessFieldRule.objects.filter(
                ruleset=self.ruleset,
                resource=resource,
                action=action,
                subject_level=self.ctx.user_level,
                is_active=True,
            )
            .order_by("field_name", "priority", "id")
        )

        if not qs.exists():
            return None

        unique_rules = {}
        for item in qs:
            if item.field_name not in unique_rules:
                unique_rules[item.field_name] = item
        return list(unique_rules.values())

    def _get_user_unit_id(self, user_obj: User):
        profile = getattr(user_obj, "profile", None)
        return getattr(profile, "unit_id", None) if profile else None

    def _legacy(self):
        from users_app.access_service import AccessService
        return AccessService(self.user)

    def _legacy_can_user(self, action: str, target_user: Optional[User] = None) -> bool:
        access = self._legacy()

        if action == "view":
            if target_user is None:
                return True
            return access.can_view_user(target_user)

        if action == "create":
            return access.can_create_user()

        if action == "update" and target_user is not None:
            return access.can_edit_user(target_user)

        if action == "delete" and target_user is not None:
            return access.can_delete_user(target_user)

        if action == "change_password" and target_user is not None:
            return access.can_change_password(target_user)

        return False

    def _legacy_visible_users(self):
        return self._legacy().get_visible_users()

    def _legacy_available_creation_units(self):
        access = self._legacy()
        available_units = [access.user_unit]
        available_units.extend(list(access.user_unit.children.all()))
        return Unit.objects.filter(id__in=[unit.id for unit in available_units]).order_by("name")