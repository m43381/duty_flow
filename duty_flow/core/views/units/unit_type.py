from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from access_control.services import AccessManager
from units.models import UnitType
from units.forms import UnitTypeForm
from core.services.unit_service import UnitTypeService


def apply_unit_type_access_to_form(form, access_manager, action: str):
    visible_fields = set(access_manager.visible_unit_type_fields(action))
    editable_fields = set(access_manager.editable_unit_type_fields(action))

    for field_name in list(form.fields.keys()):
        if field_name not in visible_fields:
            form.fields.pop(field_name, None)
            continue

        if field_name not in editable_fields:
            form.fields[field_name].disabled = True


@login_required
def unit_type_list(request):
    access = AccessManager(request.user)

    if not access.can_unit_type("view"):
        messages.error(request, "Доступ запрещён")
        return redirect("auth:dashboard")

    unit_types = access.scope_unit_types(UnitType.objects.all().order_by("level", "name"))

    search_query = request.GET.get("q", "").strip()
    if search_query:
        unit_types = unit_types.filter(name__icontains=search_query)

    return render(request, "app/unit_types/list.html", {
        "unit_types": unit_types,
        "active_tab": "unit_types",
        "page_title": "Типы подразделений",
        "page_subtitle": "Справочник типов подразделений и их уровней иерархии",
        "can_add": access.can_unit_type("create"),
        "search_query": search_query,
    })


@login_required
def unit_type_add(request):
    access = AccessManager(request.user)

    if not access.can_unit_type("create"):
        messages.error(request, "Доступ запрещён")
        return redirect("auth:dashboard")

    if request.method == "POST":
        form = UnitTypeForm(request.POST)
        apply_unit_type_access_to_form(form, access, "create")
        if form.is_valid():
            item = form.save()
            messages.success(request, f'Тип "{item.name}" создан')
            return redirect("unit_type:detail", pk=item.pk)
    else:
        form = UnitTypeForm()
        apply_unit_type_access_to_form(form, access, "create")

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
    access = AccessManager(request.user)
    item = get_object_or_404(UnitType, pk=pk)

    if not access.can_unit_type("view", item):
        messages.error(request, "Доступ запрещён")
        return redirect("auth:dashboard")

    units_count, users_count = UnitTypeService.get_usage_stats(item)

    return render(request, "app/unit_types/detail.html", {
        "item": item,
        "units_count": units_count,
        "users_count": users_count,
        "can_edit": access.can_unit_type("update", item),
        "can_delete": access.can_unit_type("delete", item),
        "active_tab": "unit_types",
        "page_title": "Типы подразделений",
        "page_subtitle": "Карточка типа подразделения",
        "title": item.name,
    })


@login_required
def unit_type_edit(request, pk):
    access = AccessManager(request.user)
    item = get_object_or_404(UnitType, pk=pk)

    if not access.can_unit_type("update", item):
        messages.error(request, "Доступ запрещён")
        return redirect("auth:dashboard")

    if request.method == "POST":
        form = UnitTypeForm(request.POST, instance=item)
        apply_unit_type_access_to_form(form, access, "update")
        if form.is_valid():
            form.save()
            messages.success(request, f'Тип "{item.name}" обновлён')
            return redirect("unit_type:detail", pk=item.pk)
    else:
        form = UnitTypeForm(instance=item)
        apply_unit_type_access_to_form(form, access, "update")

    return render(request, "app/unit_types/form.html", {
        "form": form,
        "item": item,
        "active_tab": "unit_types",
        "page_title": "Типы подразделений",
        "page_subtitle": "Редактирование типа подразделения",
        "title": "Редактировать тип подразделения",
    })


@login_required
def unit_type_delete(request, pk):
    access = AccessManager(request.user)
    item = get_object_or_404(UnitType, pk=pk)

    if not access.can_unit_type("delete", item):
        messages.error(request, "Доступ запрещён")
        return redirect("auth:dashboard")

    can_delete, error_msg = UnitTypeService.can_delete_type(item)
    if not can_delete:
        messages.error(request, error_msg)
        return redirect("unit_type:detail", pk=item.pk)

    if request.method == "POST":
        name = item.name
        item.delete()
        messages.success(request, f'Тип "{name}" удалён')
        return redirect("unit_type:list")

    return render(request, "app/unit_types/delete.html", {
        "item": item,
        "active_tab": "unit_types",
        "page_title": "Типы подразделений",
        "page_subtitle": "Удаление типа подразделения",
        "title": "Удаление типа подразделения",
    })