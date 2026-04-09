from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

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


ALLOWED_RESOURCES = {"user", "person", "unit", "unit_type"}


@level0_required
def access_dashboard(request):
    ruleset = AccessControlService.get_ruleset_for_user(request.user)
    rules_count = AccessRule.objects.filter(ruleset=ruleset).count()
    field_rules_count = AccessFieldRule.objects.filter(ruleset=ruleset).count()

    return render(request, "app/access_control/dashboard.html", {
        "ruleset": ruleset,
        "rules_count": rules_count,
        "field_rules_count": field_rules_count,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": "Права пользователей, сотрудников и подразделений",
        "title": "Управление доступом",
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

    try:
        level = int(request.GET.get("level", 0))
    except (TypeError, ValueError):
        level = 0

    if request.method == "POST":
        try:
            level = int(request.POST.get("level", 0))
        except (TypeError, ValueError):
            level = 0

        AccessControlService.save_matrix(request.user, resource, level, request.POST)
        messages.success(request, f"Права для ресурса '{resource}' и уровня {level} сохранены")
        return redirect(f"{request.path}?level={level}")

    matrix = AccessControlService.build_matrix(request.user, resource, level)

    return render(request, "app/access_control/resource_matrix.html", {
        **matrix,
        "available_levels": [0, 1, 2, 3, 4, 5],
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": f"Матрица прав: {matrix['resource_title']} / уровень {level}",
        "title": f"Матрица прав: {matrix['resource_title']}",
    })


@level0_required
def rule_list(request, resource):
    if resource not in ALLOWED_RESOURCES:
        messages.error(request, "Неизвестный ресурс")
        return redirect("access_control:dashboard")

    ruleset = AccessControlService.get_ruleset_for_user(request.user)
    items = AccessRule.objects.filter(
        ruleset=ruleset,
        resource=resource,
    ).order_by("subject_level", "action", "priority", "id")

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
    items = AccessFieldRule.objects.filter(
        ruleset=ruleset,
        resource=resource,
    ).order_by("subject_level", "action", "field_name", "priority", "id")

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