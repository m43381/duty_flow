from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from duty_types.forms import DutyTypeForm
from core.services.duty_type_service import DutyTypeService
from duty_types.models import DutyType


@login_required
def duty_type_list(request):
    """Список типов нарядов"""
    duty_types = DutyTypeService.get_user_duty_types(request.user)

    search_query = request.GET.get("q", "").strip()
    if search_query:
        duty_types = duty_types.filter(name__icontains=search_query)

    return render(request, "app/duty_types/list.html", {
        "duty_types": duty_types,
        "active_tab": "duty_types",
        "page_title": "Типы нарядов",
        "page_subtitle": "Справочник типов нарядов вашего подразделения",
        "can_add": True,
        "search_query": search_query,
    })


@login_required
def duty_type_add(request):
    """Создание типа наряда"""
    if request.method == "POST":
        form = DutyTypeForm(request.POST, user=request.user)
        if form.is_valid():
            duty_type = DutyTypeService.create_duty_type(form.cleaned_data, request.user)
            messages.success(request, f'Тип наряда "{duty_type.name}" создан')
            return redirect("type:detail", pk=duty_type.pk)
    else:
        form = DutyTypeForm(user=request.user)

    return render(request, "app/duty_types/form.html", {
        "form": form,
        "item": None,
        "active_tab": "duty_types",
        "page_title": "Типы нарядов",
        "page_subtitle": "Создание типа наряда",
        "title": "Создать тип наряда",
    })


@login_required
def duty_type_detail(request, pk):
    """Просмотр типа наряда"""
    duty_type = get_object_or_404(DutyType, pk=pk)

    if not DutyTypeService.can_edit(request.user, duty_type):
        messages.error(request, "Нет доступа")
        return redirect("type:list")

    return render(request, "app/duty_types/detail.html", {
        "item": duty_type,
        "active_tab": "duty_types",
        "page_title": "Типы нарядов",
        "page_subtitle": "Карточка типа наряда",
        "title": duty_type.name,
    })


@login_required
def duty_type_edit(request, pk):
    """Редактирование типа наряда"""
    duty_type = get_object_or_404(DutyType, pk=pk)

    if not DutyTypeService.can_edit(request.user, duty_type):
        messages.error(request, "Нет доступа")
        return redirect("type:list")

    if request.method == "POST":
        form = DutyTypeForm(request.POST, instance=duty_type, user=request.user)
        if form.is_valid():
            DutyTypeService.update_duty_type(duty_type, form.cleaned_data)
            messages.success(request, "Тип наряда обновлён")
            return redirect("type:detail", pk=duty_type.pk)
    else:
        form = DutyTypeForm(instance=duty_type, user=request.user)

    return render(request, "app/duty_types/form.html", {
        "form": form,
        "item": duty_type,
        "active_tab": "duty_types",
        "page_title": "Типы нарядов",
        "page_subtitle": "Редактирование типа наряда",
        "title": "Редактировать тип наряда",
    })


@login_required
def duty_type_delete(request, pk):
    """Удаление типа наряда"""
    duty_type = get_object_or_404(DutyType, pk=pk)

    if not DutyTypeService.can_edit(request.user, duty_type):
        messages.error(request, "Нет доступа")
        return redirect("type:list")

    if request.method == "POST":
        duty_type.delete()
        messages.success(request, "Тип наряда удалён")
        return redirect("type:list")

    return render(request, "app/duty_types/delete.html", {
        "item": duty_type,
        "active_tab": "duty_types",
        "page_title": "Типы нарядов",
        "page_subtitle": "Удаление типа наряда",
        "title": "Удаление типа наряда",
    })