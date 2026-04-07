from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from access_control.forms import AccessFieldRuleForm, AccessRuleForm
from access_control.models import AccessFieldRule, AccessRule
from core.services.access_control_service import AccessControlService


def level0_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = getattr(request.user, "profile", None)
        if not profile or profile.level != 0:
            messages.error(request, "Доступ только для уровня 0")
            return redirect("auth:dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper


@level0_required
def access_dashboard(request):
    ruleset = AccessControlService.get_ruleset_for_user(request.user)
    rules_count = AccessRule.objects.filter(ruleset=ruleset, resource="user").count()
    field_rules_count = AccessFieldRule.objects.filter(ruleset=ruleset, resource="user").count()

    return render(request, "app/access_control/dashboard.html", {
        "ruleset": ruleset,
        "rules_count": rules_count,
        "field_rules_count": field_rules_count,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": "Права пользователей",
        "title": "Права пользователей",
    })


@level0_required
def seed_user_rules(request):
    if request.method == "POST":
        AccessControlService.seed_user_rules(request.user)
        messages.success(request, "Стартовые правила для пользователей заполнены")
    return redirect("access_control:dashboard")


@level0_required
def user_access_matrix(request):
    try:
        level = int(request.GET.get("level", 0))
    except (TypeError, ValueError):
        level = 0

    if request.method == "POST":
        try:
            level = int(request.POST.get("level", 0))
        except (TypeError, ValueError):
            level = 0

        AccessControlService.save_user_access_matrix(request.user, level, request.POST)
        messages.success(request, f"Права для уровня {level} сохранены")
        return redirect(f"{request.path}?level={level}")

    matrix = AccessControlService.build_user_access_matrix(request.user, level)

    return render(request, "app/access_control/user_matrix.html", {
        **matrix,
        "available_levels": [0, 1, 2, 3, 4, 5],
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": f"Матрица прав пользователей для уровня {level}",
        "title": "Матрица прав пользователей",
    })


@level0_required
def rule_list(request):
    ruleset = AccessControlService.get_ruleset_for_user(request.user)
    items = AccessRule.objects.filter(
        ruleset=ruleset,
        resource="user",
    ).order_by("subject_level", "action", "priority", "id")

    return render(request, "app/access_control/rules/list.html", {
        "items": items,
        "ruleset": ruleset,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": "Правила доступа пользователей",
        "title": "Правила доступа",
    })


@level0_required
def rule_add(request):
    if request.method == "POST":
        form = AccessRuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Правило доступа создано")
            return redirect("access_control:rules")
    else:
        form = AccessRuleForm()

    return render(request, "app/access_control/rules/form.html", {
        "form": form,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": "Создание правила доступа",
        "title": "Создать правило доступа",
    })


@level0_required
def rule_edit(request, pk):
    item = get_object_or_404(AccessRule, pk=pk)

    if request.method == "POST":
        form = AccessRuleForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Правило доступа обновлено")
            return redirect("access_control:rules")
    else:
        form = AccessRuleForm(instance=item)

    return render(request, "app/access_control/rules/form.html", {
        "form": form,
        "item": item,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": "Редактирование правила доступа",
        "title": "Редактировать правило доступа",
    })


@level0_required
def field_rule_list(request):
    ruleset = AccessControlService.get_ruleset_for_user(request.user)
    items = AccessFieldRule.objects.filter(
        ruleset=ruleset,
        resource="user",
    ).order_by("subject_level", "action", "field_name", "priority", "id")

    return render(request, "app/access_control/field_rules/list.html", {
        "items": items,
        "ruleset": ruleset,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": "Правила полей пользователей",
        "title": "Правила полей",
    })


@level0_required
def field_rule_add(request):
    if request.method == "POST":
        form = AccessFieldRuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Правило поля создано")
            return redirect("access_control:field_rules")
    else:
        form = AccessFieldRuleForm()

    return render(request, "app/access_control/field_rules/form.html", {
        "form": form,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": "Создание правила поля",
        "title": "Создать правило поля",
    })


@level0_required
def field_rule_edit(request, pk):
    item = get_object_or_404(AccessFieldRule, pk=pk)

    if request.method == "POST":
        form = AccessFieldRuleForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Правило поля обновлено")
            return redirect("access_control:field_rules")
    else:
        form = AccessFieldRuleForm(instance=item)

    return render(request, "app/access_control/field_rules/form.html", {
        "form": form,
        "item": item,
        "active_tab": "access_control",
        "page_title": "Управление доступом",
        "page_subtitle": "Редактирование правила поля",
        "title": "Редактировать правило поля",
    })