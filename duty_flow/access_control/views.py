from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AccessFieldRuleForm, AccessRuleForm, AccessRuleSetForm
from .models import AccessFieldRule, AccessRule, AccessRuleSet


def level0_required(view_func):
    def wrapper(request, *args, **kwargs):
        profile = getattr(request.user, "profile", None)
        if not profile or profile.level != 0:
            messages.error(request, "Доступ только для пользователей верхнего уровня.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


@level0_required
def ruleset_list(request):
    items = AccessRuleSet.objects.all()
    return render(request, "app/access_control/rulesets/list.html", {"items": items})


@level0_required
def ruleset_add(request):
    if request.method == "POST":
        form = AccessRuleSetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Набор правил создан.")
            return redirect("access_control:rulesets")
    else:
        form = AccessRuleSetForm()
    return render(request, "app/access_control/rulesets/form.html", {"form": form, "title": "Новый набор правил"})


@level0_required
def rule_list(request):
    items = AccessRule.objects.select_related("ruleset").all()
    return render(request, "app/access_control/rules/list.html", {"items": items})


@level0_required
def rule_add(request):
    if request.method == "POST":
        form = AccessRuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Правило доступа создано.")
            return redirect("access_control:rules")
    else:
        form = AccessRuleForm()
    return render(request, "app/access_control/rules/form.html", {"form": form, "title": "Новое правило доступа"})


@level0_required
def rule_edit(request, pk):
    item = get_object_or_404(AccessRule, pk=pk)
    if request.method == "POST":
        form = AccessRuleForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Правило доступа обновлено.")
            return redirect("access_control:rules")
    else:
        form = AccessRuleForm(instance=item)
    return render(request, "app/access_control/rules/form.html", {"form": form, "title": "Редактирование правила"})


@level0_required
def field_rule_list(request):
    items = AccessFieldRule.objects.select_related("ruleset").all()
    return render(request, "app/access_control/field_rules/list.html", {"items": items})


@level0_required
def field_rule_add(request):
    if request.method == "POST":
        form = AccessFieldRuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Правило поля создано.")
            return redirect("access_control:field_rules")
    else:
        form = AccessFieldRuleForm()
    return render(request, "app/access_control/field_rules/form.html", {"form": form, "title": "Новое правило поля"})


@level0_required
def field_rule_edit(request, pk):
    item = get_object_or_404(AccessFieldRule, pk=pk)
    if request.method == "POST":
        form = AccessFieldRuleForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Правило поля обновлено.")
            return redirect("access_control:field_rules")
    else:
        form = AccessFieldRuleForm(instance=item)
    return render(request, "app/access_control/field_rules/form.html", {"form": form, "title": "Редактирование правила поля"})