from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError

from units.models import Unit
from units.forms import UnitForm
from core.services.unit_service import UnitService
from access_control.services import AccessManager
from access_control.services.labels import build_unit_path_label


def build_unit_breadcrumbs(unit):
    chain = []
    current = unit
    while current:
        chain.append(current)
        current = current.parent
    return list(reversed(chain))


def apply_unit_access_to_form(form, access_manager, action: str):
    visible_fields = set(access_manager.visible_unit_fields(action))
    editable_fields = set(access_manager.editable_unit_fields(action))

    for field_name in list(form.fields.keys()):
        if field_name not in visible_fields:
            form.fields.pop(field_name, None)
            continue

        if field_name not in editable_fields:
            form.fields[field_name].disabled = True

    if "parent" in form.fields:
        if action == "create":
            parents = access_manager.allowed_parents_for_unit_creation()
        else:
            parents = access_manager.allowed_parents_for_unit_update()

        form.fields["parent"].queryset = parents
        form.fields["parent"].label_from_instance = build_unit_path_label

    if "unit_type" in form.fields:
        if action == "create":
            form.fields["unit_type"].queryset = access_manager.allowed_unit_types_for_unit_creation()
        else:
            form.fields["unit_type"].queryset = access_manager.allowed_unit_types_for_unit_update()


@login_required
def unit_list(request):
    access = AccessManager(request.user)

    visible_units = access.scope_units_tree(
        Unit.objects.select_related("parent", "unit_type").all()
    )

    search_query = request.GET.get("q", "").strip()
    if search_query:
        visible_units = visible_units.filter(name__icontains=search_query)

    units_with_counts = UnitService.get_units_with_counts(visible_units)

    editable_ids = UnitService.get_editable_ids(units_with_counts, request.user)
    deletable_ids = UnitService.get_deletable_ids(units_with_counts, request.user)

    root_units = UnitService.get_root_units(
        units_with_counts,
        access.ctx.user_level,
        access.ctx.user_unit
    )

    units_tree = UnitService.build_unit_tree(
        units_with_counts,
        root_units,
        editable_ids,
        deletable_ids
    )

    can_add = access.can_unit("create")

    return render(request, "app/units/list.html", {
        "units_tree": units_tree,
        "can_add": can_add,
        "active_tab": "units",
        "page_title": "Подразделения",
        "page_subtitle": "Иерархия подразделений и переход в карточки элементов структуры",
        "search_query": search_query,
        "user_unit": access.ctx.user_unit,
        "user_level": access.ctx.user_level,
    })


@login_required
def unit_add(request):
    access = AccessManager(request.user)

    if not access.can_unit("create"):
        messages.error(request, "У вас нет прав на создание подразделений")
        return redirect("units:list")

    if request.method == "POST":
        form = UnitForm(request.POST, user=request.user)
        apply_unit_access_to_form(form, access, "create")

        if form.is_valid():
            try:
                unit = form.save()
                messages.success(request, f'Подразделение "{unit.name}" создано')
                return redirect("units:detail", pk=unit.pk)
            except IntegrityError as e:
                messages.error(request, f"Ошибка при создании подразделения: {str(e)}")
    else:
        parent_id = request.GET.get("parent")
        initial = {}

        if parent_id:
            try:
                parent = Unit.objects.get(pk=parent_id)
                allowed_parent_ids = set(
                    access.allowed_parents_for_unit_creation().values_list("id", flat=True)
                )
                if parent.id in allowed_parent_ids:
                    initial["parent"] = parent
            except Unit.DoesNotExist:
                pass

        form = UnitForm(user=request.user, initial=initial)
        apply_unit_access_to_form(form, access, "create")

    return render(request, "app/units/form.html", {
        "form": form,
        "unit": None,
        "active_tab": "units",
        "page_title": "Подразделения",
        "page_subtitle": "Создание подразделения",
        "title": "Создать подразделение",
    })


@login_required
def unit_detail(request, pk):
    access = AccessManager(request.user)
    unit = get_object_or_404(
        Unit.objects.select_related("unit_type", "parent", "parent__unit_type"),
        pk=pk
    )

    if not access.can_unit("view", unit):
        messages.error(request, "У вас нет доступа к этому подразделению")
        return redirect("units:list")

    children_qs = access.scope_units_tree(
        unit.children.select_related("unit_type", "parent").all()
    )
    children = UnitService.get_units_with_counts(children_qs)

    employees_count = unit.people.count()
    children_count = children_qs.count()
    can_edit = access.can_unit("update", unit)
    can_delete, _ = UnitService.can_delete_unit(unit, request.user)
    can_add_child = access.can_unit("create")
    breadcrumbs = build_unit_breadcrumbs(unit)

    return render(request, "app/units/detail.html", {
        "unit": unit,
        "children": children,
        "breadcrumbs": breadcrumbs,
        "employees_count": employees_count,
        "children_count": children_count,
        "can_edit": can_edit,
        "can_delete": can_delete,
        "can_add_child": can_add_child,
        "active_tab": "units",
        "page_title": "Подразделения",
        "page_subtitle": "Карточка подразделения",
        "title": unit.name,
    })


@login_required
def unit_edit(request, pk):
    access = AccessManager(request.user)
    unit = get_object_or_404(Unit, pk=pk)

    if not access.can_unit("update", unit):
        messages.error(request, "У вас нет прав на редактирование этого подразделения")
        return redirect("units:list")

    if request.method == "POST":
        form = UnitForm(request.POST, instance=unit, user=request.user)
        apply_unit_access_to_form(form, access, "update")

        if form.is_valid():
            try:
                unit = form.save()
                messages.success(request, f'Подразделение "{unit.name}" обновлено')
                return redirect("units:detail", pk=unit.pk)
            except IntegrityError as e:
                messages.error(request, f"Ошибка при обновлении подразделения: {str(e)}")
    else:
        form = UnitForm(instance=unit, user=request.user)
        apply_unit_access_to_form(form, access, "update")

    return render(request, "app/units/form.html", {
        "form": form,
        "unit": unit,
        "active_tab": "units",
        "page_title": "Подразделения",
        "page_subtitle": "Редактирование подразделения",
        "title": "Редактировать подразделение",
    })


@login_required
def unit_delete(request, pk):
    unit = get_object_or_404(Unit, pk=pk)

    can_delete, error_msg = UnitService.can_delete_unit(unit, request.user)

    if not can_delete:
        messages.error(request, error_msg)
        return redirect("units:detail", pk=unit.pk)

    if request.method == "POST":
        unit_name = unit.name
        unit.delete()
        messages.success(request, f'Подразделение "{unit_name}" удалено')
        return redirect("units:list")

    return render(request, "app/units/delete.html", {
        "unit": unit,
        "active_tab": "units",
        "page_title": "Подразделения",
        "page_subtitle": "Удаление подразделения",
        "title": "Удаление подразделения",
    })