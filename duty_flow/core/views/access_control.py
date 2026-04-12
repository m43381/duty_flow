from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from users_app.models import UserProfile
from units.models import UnitType
from access_control.forms import AccessFieldRuleForm, AccessRuleForm
from access_control.models import AccessFieldRule, AccessRule
from core.services.access_control import AccessControlService


def level0_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = getattr(request.user, "profile", None)
        if not profile or profile.level != 0:
            messages.error(request, "Доступ только для уровня 0")
            return redirect("auth:dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper


ALLOWED_RESOURCES = {"user", "person", "unit", "unit_type", "duty_type", "plan", "assignment"}


def _get_available_levels():
    from users_app.models import UserProfile

    levels = list(
        UserProfile.objects
        .filter(unit__isnull=False, unit__unit_type__isnull=False)
        .values_list("unit__unit_type__level", flat=True)
        .distinct()
    )

    levels = sorted(level for level in levels if level is not None)
    return levels

def _get_level_labels(levels):
    result = {}

    for level in levels:
        names = list(
            UnitType.objects
            .filter(level=level)
            .values_list("name", flat=True)
            .distinct()
            .order_by("name")
        )

        if not names:
            result[level] = f"Уровень {level}"
        elif len(names) == 1:
            result[level] = names[0]
        else:
            result[level] = ", ".join(names)

    return result


@level0_required
def access_dashboard(request):
    ruleset = AccessControlService.get_ruleset_for_user(request.user)
    rules_count = AccessRule.objects.filter(ruleset=ruleset).count()
    field_rules_count = AccessFieldRule.objects.filter(ruleset=ruleset).count()

    resource_cards = [
        {"code": "user", "title": "Пользователи", "seed_label": "users"},
        {"code": "person", "title": "Сотрудники", "seed_label": "people"},
        {"code": "unit", "title": "Подразделения", "seed_label": "units"},
        {"code": "unit_type", "title": "Типы подразделений", "seed_label": "unit_types"},
        {"code": "duty_type", "title": "Типы нарядов", "seed_label": "duty_types"},
        {"code": "plan", "title": "Планы нарядов", "seed_label": "plans"},
        {"code": "assignment", "title": "Назначения сотрудников", "seed_label": "assignments"},
    ]

    return render(request, "app/access_control/dashboard.html", {
        "ruleset": ruleset,
        "rules_count": rules_count,
        "field_rules_count": field_rules_count,
        "resource_cards": resource_cards,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": "Настройка прав и ограничений",
        "title": "Управление доступом",
    })


@level0_required
def access_diagnostics(request):
    resource = request.GET.get("resource", "user")
    user_id = request.GET.get("user_id")

    diagnostics = None
    target_user = None

    if user_id:
        try:
            target_user = User.objects.select_related("profile", "profile__unit").get(pk=user_id)
            diagnostics = AccessControlService.build_diagnostics(target_user, resource)
        except User.DoesNotExist:
            messages.error(request, "Пользователь не найден")

    users = User.objects.select_related("profile", "profile__unit").order_by("username")
    resources = AccessControlService.get_supported_resources()

    return render(request, "app/access_control/diagnostics.html", {
        "users": users,
        "resources": resources,
        "selected_resource": resource,
        "selected_user_id": int(user_id) if user_id and user_id.isdigit() else None,
        "diagnostics": diagnostics,
        "active_tab": "access_control",
        "page_title": "Диагностика доступа",
        "page_subtitle": "Проверка фактических прав конкретного пользователя",
        "title": "Диагностика доступа",
    })


@level0_required
def seed_resource_rules(request, resource):
    if resource not in ALLOWED_RESOURCES:
        messages.error(request, "Неизвестный ресурс")
        return redirect("access_control:dashboard")

    if request.method == "POST":
        AccessControlService.seed_rules(request.user, resource)
        messages.success(request, f"Стартовые правила для ресурса '{resource}' заполнены")

    return redirect("access_control:dashboard")


@level0_required
def resource_matrix(request, resource):
    if resource not in ALLOWED_RESOURCES:
        messages.error(request, "Неизвестный ресурс")
        return redirect("access_control:dashboard")

    available_levels = _get_available_levels()
    level_labels = _get_level_labels(available_levels)

    try:
        default_level = available_levels[0] if available_levels else 0
        level = int(request.GET.get("level", default_level))
    except (TypeError, ValueError):
        level = default_level if available_levels else 0

    if level not in available_levels:
        available_levels = sorted(set(available_levels + [level]))

    if request.method == "POST":
        try:
            level = int(request.POST.get("level", level))
        except (TypeError, ValueError):
            pass

        if level not in available_levels:
            available_levels = sorted(set(available_levels + [level]))

        AccessControlService.save_matrix(request.user, resource, level, request.POST)
        messages.success(request, f"Права для ресурса '{resource}' и уровня {level} сохранены")
        return redirect(f"{request.path}?level={level}")

    matrix = AccessControlService.build_matrix(request.user, resource, level)

    return render(request, "app/access_control/resource_matrix.html", {
        **matrix,
        "available_levels": available_levels,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": f"Матрица прав: {matrix['resource_title']} / уровень {level}",
        "title": f"Матрица прав: {matrix['resource_title']}",
        "level_labels": level_labels,
    })


@level0_required
def rule_list(request, resource):
    if resource not in ALLOWED_RESOURCES:
        messages.error(request, "Неизвестный ресурс")
        return redirect("access_control:dashboard")

    ruleset = AccessControlService.get_ruleset_for_user(request.user)
    items = AccessRule.objects.filter(ruleset=ruleset, resource=resource).order_by("subject_level", "action", "priority", "id")

    return render(request, "app/access_control/rules/list.html", {
        "items": items,
        "ruleset": ruleset,
        "resource": resource,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": f"Правила доступа: {resource}",
        "title": "Правила доступа",
    })


@level0_required
def rule_add(request, resource):
    if resource not in ALLOWED_RESOURCES:
        messages.error(request, "Неизвестный ресурс")
        return redirect("access_control:dashboard")

    if request.method == "POST":
        form = AccessRuleForm(request.POST, resource=resource)
        if form.is_valid():
            form.save()
            messages.success(request, "Правило доступа создано")
            return redirect("access_control:rules", resource=resource)
    else:
        form = AccessRuleForm(resource=resource)

    return render(request, "app/access_control/rules/form.html", {
        "form": form,
        "resource": resource,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": "Создание правила доступа",
        "title": "Создать правило доступа",
    })


@level0_required
def rule_edit(request, resource, pk):
    if resource not in ALLOWED_RESOURCES:
        messages.error(request, "Неизвестный ресурс")
        return redirect("access_control:dashboard")

    item = get_object_or_404(AccessRule, pk=pk, resource=resource)

    if request.method == "POST":
        form = AccessRuleForm(request.POST, instance=item, resource=resource)
        if form.is_valid():
            form.save()
            messages.success(request, "Правило доступа обновлено")
            return redirect("access_control:rules", resource=resource)
    else:
        form = AccessRuleForm(instance=item, resource=resource)

    return render(request, "app/access_control/rules/form.html", {
        "form": form,
        "item": item,
        "resource": resource,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": "Редактирование правила доступа",
        "title": "Редактировать правило доступа",
    })


@level0_required
def field_rule_list(request, resource):
    if resource not in ALLOWED_RESOURCES:
        messages.error(request, "Неизвестный ресурс")
        return redirect("access_control:dashboard")

    ruleset = AccessControlService.get_ruleset_for_user(request.user)
    items = AccessFieldRule.objects.filter(ruleset=ruleset, resource=resource).order_by("subject_level", "action", "field_name", "priority", "id")

    return render(request, "app/access_control/field_rules/list.html", {
        "items": items,
        "ruleset": ruleset,
        "resource": resource,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": f"Правила полей: {resource}",
        "title": "Правила полей",
    })


@level0_required
def field_rule_add(request, resource):
    if resource not in ALLOWED_RESOURCES:
        messages.error(request, "Неизвестный ресурс")
        return redirect("access_control:dashboard")

    if request.method == "POST":
        form = AccessFieldRuleForm(request.POST, resource=resource)
        if form.is_valid():
            form.save()
            messages.success(request, "Правило поля создано")
            return redirect("access_control:field_rules", resource=resource)
    else:
        form = AccessFieldRuleForm(resource=resource)

    return render(request, "app/access_control/field_rules/form.html", {
        "form": form,
        "resource": resource,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": "Создание правила поля",
        "title": "Создать правило поля",
    })


@level0_required
def field_rule_edit(request, resource, pk):
    if resource not in ALLOWED_RESOURCES:
        messages.error(request, "Неизвестный ресурс")
        return redirect("access_control:dashboard")

    item = get_object_or_404(AccessFieldRule, pk=pk, resource=resource)

    if request.method == "POST":
        form = AccessFieldRuleForm(request.POST, instance=item, resource=resource)
        if form.is_valid():
            form.save()
            messages.success(request, "Правило поля обновлено")
            return redirect("access_control:field_rules", resource=resource)
    else:
        form = AccessFieldRuleForm(instance=item, resource=resource)

    return render(request, "app/access_control/field_rules/form.html", {
        "form": form,
        "item": item,
        "resource": resource,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": "Редактирование правила поля",
        "title": "Редактировать правило поля",
    })