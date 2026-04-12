from django.urls import reverse

from access_control.models import AccessMenuRule, AccessRule, AccessRuleSet
from .manager import AccessManager


MENU_ITEMS = [
    {
        "key": "dashboard",
        "title": "Дашборд",
        "icon": "📊",
        "url_name": "auth:dashboard",
        "section": "main",
        "active_tab": "dashboard",
        "namespace": "auth",
    },
    {
        "key": "people",
        "title": "Сотрудники",
        "icon": "👥",
        "url_name": "people:person_list",
        "section": "main",
        "active_tab": "people",
        "namespace": "people",
    },
    {
        "key": "plans",
        "title": "Планы нарядов",
        "icon": "📋",
        "url_name": "plan:list",
        "section": "main",
        "active_tab": "plans",
        "namespace": "plan",
    },
    {
        "key": "assignments",
        "title": "Назначения",
        "icon": "🗓️",
        "url_name": "assignment:calendar",
        "section": "main",
        "active_tab": "assignments",
        "namespace": "assignment",
    },
    {
        "key": "duty_types",
        "title": "Типы нарядов",
        "icon": "📌",
        "url_name": "type:list",
        "section": "directories",
        "active_tab": "duty_types",
        "namespace": "type",
    },
    {
        "key": "unit_types",
        "title": "Типы подразделений",
        "icon": "🏷️",
        "url_name": "unit_type:list",
        "section": "directories",
        "active_tab": "unit_types",
        "namespace": "unit_type",
    },
    {
        "key": "units",
        "title": "Подразделения",
        "icon": "🏛️",
        "url_name": "units:list",
        "section": "directories",
        "active_tab": "units",
        "namespace": "units",
    },
    {
        "key": "users",
        "title": "Пользователи",
        "icon": "👤",
        "url_name": "users:list",
        "section": "directories",
        "active_tab": "users",
        "namespace": "users",
    },
    {
        "key": "access_control",
        "title": "Управление доступом",
        "icon": "🔐",
        "url_name": "access_control:dashboard",
        "section": "directories",
        "active_tab": "access_control",
        "namespace": "access_control",
    },
]


SECTION_TITLES = {
    "main": "Основное",
    "directories": "Справочники",
}


MENU_ACCESS_MAP = {
    "dashboard": None,
    "people": ("person", "view"),
    "plans": ("plan", "view"),
    "assignments": ("assignment", "view"),
    "duty_types": ("duty_type", "view"),
    "unit_types": ("unit_type", "view"),
    "units": ("unit", "view"),
    "users": ("user", "view"),
    "access_control": None,
}


NAMESPACE_TO_MENU_KEY = {
    "people": "people",
    "plan": "plans",
    "assignment": "assignments",
    "type": "duty_types",
    "unit_type": "unit_types",
    "units": "units",
    "users": "users",
    "access_control": "access_control",
}


def get_effective_level(user):
    profile = getattr(user, "profile", None)
    if not profile:
        return None

    unit = getattr(profile, "unit", None)
    if unit and getattr(unit, "unit_type", None):
        return unit.unit_type.level

    return getattr(profile, "level", None)


def _get_ruleset():
    return AccessRuleSet.get_default()


def _get_first_rule(ruleset, resource, action, level):
    return (
        AccessRule.objects.filter(
            ruleset=ruleset,
            resource=resource,
            action=action,
            subject_level=level,
            is_active=True,
        )
        .order_by("priority", "id")
        .first()
    )


def _default_menu_visibility_for_level(ruleset, menu_key, level):
    if menu_key == "dashboard":
        return True

    if menu_key == "access_control":
        return level == 0

    resource_action = MENU_ACCESS_MAP.get(menu_key)
    if not resource_action:
        return False

    resource, action = resource_action
    rule = _get_first_rule(ruleset, resource, action, level)

    if rule:
        return bool(rule.is_allowed)

    return False


def get_menu_visibility_for_level(ruleset, menu_key, level):
    if menu_key == "access_control" and level == 0:
        return True

    explicit_rule = (
        AccessMenuRule.objects.filter(
            ruleset=ruleset,
            menu_key=menu_key,
            subject_level=level,
            is_active=True,
        )
        .order_by("priority", "id")
        .first()
    )

    if explicit_rule:
        if menu_key == "access_control" and level == 0:
            return True
        return explicit_rule.is_visible

    return _default_menu_visibility_for_level(ruleset, menu_key, level)


def build_navigation_visibility(user):
    access = AccessManager(user)
    ruleset = access.ruleset
    level = get_effective_level(user)

    result = {}
    for item in MENU_ITEMS:
        result[item["key"]] = get_menu_visibility_for_level(ruleset, item["key"], level)

    return result


def build_navigation_sections(user):
    visibility = build_navigation_visibility(user)

    sections = []
    for section_key, section_title in SECTION_TITLES.items():
        items = []
        for item in MENU_ITEMS:
            if item["section"] != section_key:
                continue
            if not visibility.get(item["key"], False):
                continue

            items.append({
                "key": item["key"],
                "title": item["title"],
                "icon": item["icon"],
                "url": reverse(item["url_name"]),
                "active_tab": item["active_tab"],
            })

        if items:
            sections.append({
                "key": section_key,
                "title": section_title,
                "items": items,
            })

    return sections


def build_menu_matrix(user):
    access = AccessManager(user)
    ruleset = access.ruleset

    from users_app.models import UserProfile

    levels = sorted(
        set(
            UserProfile.objects
            .filter(unit__isnull=False, unit__unit_type__isnull=False)
            .values_list("unit__unit_type__level", flat=True)
            .distinct()
        )
    )

    existing_rules = {
        (rule.menu_key, rule.subject_level): rule
        for rule in AccessMenuRule.objects.filter(ruleset=ruleset, is_active=True)
    }

    rows = []
    for item in MENU_ITEMS:
        cells = []
        for level in levels:
            rule = existing_rules.get((item["key"], level))

            effective_value = get_menu_visibility_for_level(ruleset, item["key"], level)

            cells.append({
                "level": level,
                "is_visible": effective_value,
                "has_explicit_rule": rule is not None,
            })

        rows.append({
            "key": item["key"],
            "title": item["title"],
            "icon": item["icon"],
            "section": SECTION_TITLES[item["section"]],
            "cells": cells,
        })

    return {
        "ruleset": ruleset,
        "levels": levels,
        "rows": rows,
    }


def save_menu_matrix(user, post_data):
    access = AccessManager(user)
    ruleset = access.ruleset
    matrix = build_menu_matrix(user)
    levels = matrix["levels"]

    for item in MENU_ITEMS:
        for level in levels:
            key = f"menu__{item['key']}__{level}"
            is_visible = key in post_data

            if item["key"] == "access_control" and level == 0:
                is_visible = True

            AccessMenuRule.objects.update_or_create(
                ruleset=ruleset,
                menu_key=item["key"],
                subject_level=level,
                defaults={
                    "is_visible": is_visible,
                    "is_active": True,
                    "priority": 100,
                },
            )


def get_menu_key_by_namespace(namespace):
    return NAMESPACE_TO_MENU_KEY.get(namespace)