from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from units.models import UnitType
from units.forms import UnitTypeForm
from core.services.unit_service import UnitTypeService


@login_required
def unit_type_list(request):
    """Список типов подразделений"""
    if not UnitTypeService.can_manage(request.user):
        messages.error(request, "Доступ только для администраторов")
        return redirect("auth:dashboard")

    unit_types = UnitType.objects.all().order_by("level", "name")

    search_query = request.GET.get("q", "").strip()
    if search_query:
        unit_types = unit_types.filter(name__icontains=search_query)

    return render(request, "app/unit_types/list.html", {
        "unit_types": unit_types,
        "active_tab": "unit_types",
        "page_title": "Типы подразделений",
        "page_subtitle": "Справочник типов подразделений и их уровней иерархии",
        "can_add": True,
        "search_query": search_query,
    })


@login_required
def unit_type_add(request):
    """Создание типа подразделения"""
    if not UnitTypeService.can_manage(request.user):
        messages.error(request, "Доступ только для администраторов")
        return redirect("auth:dashboard")

    if request.method == "POST":
        form = UnitTypeForm(request.POST)
        if form.is_valid():
            unit_type = form.save()
            messages.success(request, f'Тип "{unit_type.name}" создан')
            return redirect("unit_type:detail", pk=unit_type.pk)
    else:
        form = UnitTypeForm()

    return render(request, "app/unit_types/form.html", {
        "form": form,
        "item": None,
        "active_tab": "unit_types",
        "page_title": "Типы подразделений",
        "page_subtitle": "Создание типа подразделения",
        "title": "Создать тип подразделения",
    })


@login_required
def unit_type_detail(request, pk):
    """Просмотр типа подразделения"""
    if not UnitTypeService.can_manage(request.user):
        messages.error(request, "Доступ только для администраторов")
        return redirect("auth:dashboard")

    unit_type = get_object_or_404(UnitType, pk=pk)
    units_count, users_count = UnitTypeService.get_usage_stats(unit_type)

    return render(request, "app/unit_types/detail.html", {
        "item": unit_type,
        "units_count": units_count,
        "users_count": users_count,
        "active_tab": "unit_types",
        "page_title": "Типы подразделений",
        "page_subtitle": "Карточка типа подразделения",
        "title": unit_type.name,
    })


@login_required
def unit_type_edit(request, pk):
    """Редактирование типа подразделения"""
    if not UnitTypeService.can_manage(request.user):
        messages.error(request, "Доступ только для администраторов")
        return redirect("auth:dashboard")

    unit_type = get_object_or_404(UnitType, pk=pk)

    if request.method == "POST":
        form = UnitTypeForm(request.POST, instance=unit_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'Тип "{unit_type.name}" обновлен')
            return redirect("unit_type:detail", pk=unit_type.pk)
    else:
        form = UnitTypeForm(instance=unit_type)

    return render(request, "app/unit_types/form.html", {
        "form": form,
        "item": unit_type,
        "active_tab": "unit_types",
        "page_title": "Типы подразделений",
        "page_subtitle": "Редактирование типа подразделения",
        "title": "Редактировать тип подразделения",
    })


@login_required
def unit_type_delete(request, pk):
    """Удаление типа подразделения"""
    if not UnitTypeService.can_manage(request.user):
        messages.error(request, "Доступ только для администраторов")
        return redirect("auth:dashboard")

    unit_type = get_object_or_404(UnitType, pk=pk)

    can_delete, error_msg = UnitTypeService.can_delete_type(unit_type)
    if not can_delete:
        messages.error(request, error_msg)
        return redirect("unit_type:detail", pk=unit_type.pk)

    if request.method == "POST":
        unit_type.delete()
        messages.success(request, f'Тип "{unit_type.name}" удален')
        return redirect("unit_type:list")

    return render(request, "app/unit_types/delete.html", {
        "item": unit_type,
        "active_tab": "unit_types",
        "page_title": "Типы подразделений",
        "page_subtitle": "Удаление типа подразделения",
        "title": "Удаление типа подразделения",
    })