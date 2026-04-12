from django.urls import reverse

from access_control.models import AccessMenuRule
from access_control.services import AccessManager


MENU_ITEMS = [
    {
        "key": "dashboard",
        "title": "Дашборд",
        "icon": "📊",
        "url_name": "auth:dashboard",
        "section": "main",
        "active_tab": "dashboard",
    },
    {
        "key": "people",
        "title": "Сотрудники",
        "icon": "👥",
        "url_name": "people:person_list",
        "section": "main",
        "active_tab": "people",
    },
    {
        "key": "plans",
        "title": "Планы нарядов",
        "icon": "📋",
        "url_name": "plan:list",
        "section": "main",
        "active_tab": "plans",
    },
    {
        "key": "assignments",
        "title": "Назначения",
        "icon": "🗓️",
        "url_name": "assignment:calendar",
        "section": "main",
        "active_tab": "assignments",
    },
    {
        "key": "duty_types",
        "title": "Типы нарядов",
        "icon": "📌",
        "url_name": "type:list",
        "section": "directories",
        "active_tab": "duty_types",
    },
    {
        "key": "unit_types",
        "title": "Типы подразделений",
        "icon": "🏷️",
        "url_name": "unit_type:list",
        "section": "directories",
        "active_tab": "unit_types",
    },
    {
        "key": "units",
        "title": "Подразделения",
        "icon": "🏛️",
        "url_name": "units:list",
        "section": "directories",
        "active_tab": "units",
    },
    {
        "key": "users",
        "title": "Пользователи",
        "icon": "👤",
        "url_name": "users:list",
        "section": "directories",
        "active_tab": "users",
    },
    {
        "key": "access_control",
        "title": "Управление доступом",
        "icon": "🔐",
        "url_name": "access_control:dashboard",
        "section": "directories",
        "active_tab": "access_control",
    },
]


SECTION_TITLES = {
    "main": "Основное",
    "directories": "Справочники",
}


def get_effective_level(user):
    profile = getattr(user, "profile", None)
    if not profile:
        return None

    unit = getattr(profile, "unit", None)
    if unit and getattr(unit, "unit_type", None):
        return unit.unit_type.level

    return getattr(profile, "level", None)


def _fallback_visibility(user, key):
    access = AccessManager(user)
    level = get_effective_level(user)

    if key == "dashboard":
        return True
    if key == "people":
        return access.can_person("view")
    if key == "plans":
        return access.can_plan("view")
    if key == "assignments":
        return access.can_assignment("view")
    if key == "duty_types":
        return access.can_duty_type("view")
    if key == "unit_types":
        return access.can_unit_type("view")
    if key == "units":
        return access.can_unit("view")
    if key == "users":
        return access.can_user("view")
    if key == "access_control":
        return level == 0

    return False


def build_navigation_visibility(user):
    access = AccessManager(user)
    ruleset = access.ruleset
    level = get_effective_level(user)

    explicit_rules = {
        item.menu_key: item.is_visible
        for item in AccessMenuRule.objects.filter(
            ruleset=ruleset,
            subject_level=level,
            is_active=True,
        )
    }

    result = {}
    for item in MENU_ITEMS:
        if item["key"] in explicit_rules:
            result[item["key"]] = explicit_rules[item["key"]]
        else:
            result[item["key"]] = _fallback_visibility(user, item["key"])

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
            if rule:
                is_visible = rule.is_visible
                source = "rule"
            else:
                is_visible = _fallback_visibility(user, item["key"]) if get_effective_level(user) == level else False
                source = "default"

            cells.append({
                "level": level,
                "is_visible": is_visible,
                "source": source,
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