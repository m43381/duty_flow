from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError

from units.models import Unit
from units.forms import UnitForm
from users_app.access_service import AccessService
from core.services.unit_service import UnitService


def build_unit_breadcrumbs(unit):
    chain = []
    current = unit
    while current:
        chain.append(current)
        current = current.parent
    return list(reversed(chain))


@login_required
def unit_list(request):
    """Дерево подразделений"""
    access = AccessService(request.user)

    visible_units = access.get_visible_units()

    search_query = request.GET.get("q", "").strip()
    if search_query:
        visible_units = visible_units.filter(name__icontains=search_query)

    units_with_counts = UnitService.get_units_with_counts(visible_units)

    editable_ids = UnitService.get_editable_ids(units_with_counts, request.user)
    deletable_ids = UnitService.get_deletable_ids(units_with_counts, request.user)

    root_units = UnitService.get_root_units(
        units_with_counts,
        access.user_level,
        access.user_unit
    )

    units_tree = UnitService.build_unit_tree(
        units_with_counts,
        root_units,
        editable_ids,
        deletable_ids
    )

    can_add = access.get_available_parents_for_creation().exists()

    return render(request, "app/units/list.html", {
        "units_tree": units_tree,
        "can_add": can_add,
        "active_tab": "units",
        "page_title": "Подразделения",
        "page_subtitle": "Иерархия подразделений и переход в карточки элементов структуры",
        "search_query": search_query,
        "user_unit": access.user_unit,
        "user_level": access.user_level,
    })


@login_required
def unit_add(request):
    """Создание подразделения"""
    access = AccessService(request.user)

    if not access.get_available_parents_for_creation().exists():
        messages.error(request, "У вас нет прав на создание подразделений")
        return redirect("units:list")

    if request.method == "POST":
        form = UnitForm(request.POST, user=request.user)
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
                if access.can_create_in_unit(parent):
                    initial["parent"] = parent
            except Unit.DoesNotExist:
                pass
        form = UnitForm(user=request.user, initial=initial)

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
    """Просмотр подразделения"""
    access = AccessService(request.user)
    unit = get_object_or_404(
        Unit.objects.select_related("unit_type", "parent", "parent__unit_type"),
        pk=pk
    )

    if not access.can_view_unit(unit):
        messages.error(request, "У вас нет доступа к этому подразделению")
        return redirect("units:list")

    children_qs = unit.children.select_related("unit_type", "parent").all()
    children = UnitService.get_units_with_counts(children_qs)

    employees_count = unit.people.count()
    children_count = children_qs.count()
    can_edit = access.can_edit_unit(unit)
    can_delete, _ = UnitService.can_delete_unit(unit, request.user)
    can_add_child = access.can_create_in_unit(unit)
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
    """Редактирование подразделения"""
    access = AccessService(request.user)
    unit = get_object_or_404(Unit, pk=pk)

    if not access.can_edit_unit(unit):
        messages.error(request, "У вас нет прав на редактирование этого подразделения")
        return redirect("units:list")

    if request.method == "POST":
        form = UnitForm(request.POST, instance=unit, user=request.user)
        if form.is_valid():
            try:
                unit = form.save()
                messages.success(request, f'Подразделение "{unit.name}" обновлено')
                return redirect("units:detail", pk=unit.pk)
            except IntegrityError as e:
                messages.error(request, f"Ошибка при обновлении подразделения: {str(e)}")
    else:
        form = UnitForm(instance=unit, user=request.user)

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
    """Удаление подразделения"""
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