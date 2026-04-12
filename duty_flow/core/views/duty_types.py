from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from access_control.services import AccessManager
from access_control.services.labels import build_unit_path_label
from duty_types.forms import DutyTypeForm
from duty_types.models import DutyType
from core.services.duty_type_service import DutyTypeService


def apply_duty_type_access_to_form(form, access_manager, action: str):
    visible_fields = set(access_manager.visible_duty_type_fields(action))
    editable_fields = set(access_manager.editable_duty_type_fields(action))

    for field_name in list(form.fields.keys()):
        if field_name not in visible_fields:
            form.fields.pop(field_name, None)
            continue

        if field_name not in editable_fields:
            form.fields[field_name].disabled = True

    if "unit" in form.fields:
        if action == "create":
            units = access_manager.allowed_units_for_duty_type_creation()
        else:
            units = access_manager.allowed_units_for_duty_type_update()

        if hasattr(form.fields["unit"], "queryset"):
            form.fields["unit"].queryset = units
            form.fields["unit"].label_from_instance = build_unit_path_label


@login_required
def duty_type_list(request):
    access = AccessManager(request.user)
    duty_types = access.scope_duty_types(
        DutyType.objects.select_related("unit", "created_by_unit").all()
    )

    search_query = request.GET.get("q", "").strip()
    if search_query:
        duty_types = duty_types.filter(name__icontains=search_query)

    return render(request, "app/duty_types/list.html", {
        "duty_types": duty_types,
        "active_tab": "duty_types",
        "page_title": "Типы нарядов",
        "page_subtitle": "Справочник типов нарядов",
        "can_add": access.can_duty_type("create"),
        "search_query": search_query,
    })


@login_required
def duty_type_add(request):
    access = AccessManager(request.user)

    if not access.can_duty_type("create"):
        messages.error(request, "Нет доступа")
        return redirect("type:list")

    if request.method == "POST":
        form = DutyTypeForm(request.POST, user=request.user)
        apply_duty_type_access_to_form(form, access, "create")

        if form.is_valid():
            item = DutyTypeService.create_duty_type(form.cleaned_data, request.user)
            messages.success(request, f'Тип наряда "{item.name}" создан')
            return redirect("type:detail", pk=item.pk)
    else:
        form = DutyTypeForm(user=request.user)
        apply_duty_type_access_to_form(form, access, "create")

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
    access = AccessManager(request.user)
    item = get_object_or_404(
        DutyType.objects.select_related("unit", "created_by_unit"),
        pk=pk
    )

    if not access.can_duty_type("view", item):
        messages.error(request, "Нет доступа")
        return redirect("type:list")

    return render(request, "app/duty_types/detail.html", {
        "item": item,
        "can_edit": access.can_duty_type("update", item),
        "can_delete": access.can_duty_type("delete", item),
        "active_tab": "duty_types",
        "page_title": "Типы нарядов",
        "page_subtitle": "Карточка типа наряда",
        "title": item.name,
    })


@login_required
def duty_type_edit(request, pk):
    access = AccessManager(request.user)
    item = get_object_or_404(DutyType, pk=pk)

    if not access.can_duty_type("update", item):
        messages.error(request, "Нет доступа")
        return redirect("type:list")

    if request.method == "POST":
        form = DutyTypeForm(request.POST, instance=item, user=request.user)
        apply_duty_type_access_to_form(form, access, "update")

        if form.is_valid():
            DutyTypeService.update_duty_type(item, form.cleaned_data)
            messages.success(request, "Тип наряда обновлён")
            return redirect("type:detail", pk=item.pk)
    else:
        form = DutyTypeForm(instance=item, user=request.user)
        apply_duty_type_access_to_form(form, access, "update")

    return render(request, "app/duty_types/form.html", {
        "form": form,
        "item": item,
        "active_tab": "duty_types",
        "page_title": "Типы нарядов",
        "page_subtitle": "Редактирование типа наряда",
        "title": "Редактировать тип наряда",
    })


@login_required
def duty_type_delete(request, pk):
    access = AccessManager(request.user)
    item = get_object_or_404(DutyType, pk=pk)

    if not access.can_duty_type("delete", item):
        messages.error(request, "Нет доступа")
        return redirect("type:list")

    if request.method == "POST":
        name = item.name
        item.delete()
        messages.success(request, f'Тип наряда "{name}" удалён')
        return redirect("type:list")

    return render(request, "app/duty_types/delete.html", {
        "item": item,
        "active_tab": "duty_types",
        "page_title": "Типы нарядов",
        "page_subtitle": "Удаление типа наряда",
        "title": "Удаление типа наряда",
    })