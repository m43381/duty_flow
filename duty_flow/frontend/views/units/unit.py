from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError

from units.models import Unit
from units.forms import UnitForm
from users_app.access_service import AccessService
from frontend.services.unit_service import UnitService


@login_required
def unit_list(request):
    """Список/дерево подразделений"""
    access = AccessService(request.user)
    
    # Получаем видимые подразделения
    visible_units = access.get_visible_units()
    
    # Поиск по названию
    search_query = request.GET.get('search', '').strip()
    if search_query:
        visible_units = visible_units.filter(name__icontains=search_query)
    
    # Добавляем количество сотрудников
    units_with_counts = UnitService.get_units_with_counts(visible_units)
    
    # Получаем права
    editable_ids = UnitService.get_editable_ids(units_with_counts, request.user)
    deletable_ids = UnitService.get_deletable_ids(units_with_counts, request.user)
    
    # Определяем корневые узлы
    root_units = UnitService.get_root_units(
        units_with_counts, 
        access.user_level, 
        access.user_unit
    )
    
    # Строим дерево
    units_tree = UnitService.build_unit_tree(
        units_with_counts, 
        root_units, 
        editable_ids, 
        deletable_ids
    )
    
    # Проверка права на создание
    can_create = access.get_available_parents_for_creation().exists()
    
    return render(request, 'units/list.html', {
        'units_tree': units_tree,
        'show_as_tree': True,
        'can_add': can_create,
        'active_tab': 'units',
        'title': 'Подразделения',
        'search_query': search_query,
        'user_unit': access.user_unit,
        'user_level': access.user_level,
    })


@login_required
def unit_add(request):
    """Создание подразделения"""
    access = AccessService(request.user)
    
    if not access.get_available_parents_for_creation().exists():
        messages.error(request, 'У вас нет прав на создание подразделений')
        return redirect('units:list')
    
    if request.method == 'POST':
        form = UnitForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                unit = form.save()
                messages.success(request, f'Подразделение "{unit.name}" создано')
                return redirect('units:detail', pk=unit.pk)
            except IntegrityError as e:
                messages.error(request, f'Ошибка при создании подразделения: {str(e)}')
    else:
        parent_id = request.GET.get('parent')
        initial = {}
        if parent_id:
            try:
                parent = Unit.objects.get(pk=parent_id)
                if access.can_create_in_unit(parent):
                    initial['parent'] = parent
            except Unit.DoesNotExist:
                pass
        form = UnitForm(user=request.user, initial=initial)
    
    return render(request, 'units/form.html', {
        'form': form,
        'active_tab': 'units',
        'title': 'Создание подразделения',
    })


@login_required
def unit_detail(request, pk):
    """Просмотр подразделения"""
    access = AccessService(request.user)
    unit = get_object_or_404(Unit, pk=pk)
    
    if not access.can_view_unit(unit):
        messages.error(request, 'У вас нет доступа к этому подразделению')
        return redirect('units:list')
    
    employees_count = unit.people.count()
    children_count = unit.children.count()
    can_edit = access.can_edit_unit(unit)
    can_delete, _ = UnitService.can_delete_unit(unit, request.user)
    
    return render(request, 'units/detail.html', {
        'unit': unit,
        'employees_count': employees_count,
        'children_count': children_count,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'active_tab': 'units',
        'title': unit.name,
    })


@login_required
def unit_edit(request, pk):
    """Редактирование подразделения"""
    access = AccessService(request.user)
    unit = get_object_or_404(Unit, pk=pk)
    
    if not access.can_edit_unit(unit):
        messages.error(request, 'У вас нет прав на редактирование этого подразделения')
        return redirect('units:list')
    
    if request.method == 'POST':
        form = UnitForm(request.POST, instance=unit, user=request.user)
        if form.is_valid():
            try:
                unit = form.save()
                messages.success(request, f'Подразделение "{unit.name}" обновлено')
                return redirect('units:detail', pk=unit.pk)
            except IntegrityError as e:
                messages.error(request, f'Ошибка при обновлении подразделения: {str(e)}')
    else:
        form = UnitForm(instance=unit, user=request.user)
    
    return render(request, 'units/form.html', {
        'form': form,
        'unit': unit,
        'active_tab': 'units',
        'title': 'Редактирование подразделения',
    })


@login_required
def unit_delete(request, pk):
    """Удаление подразделения"""
    access = AccessService(request.user)
    unit = get_object_or_404(Unit, pk=pk)
    
    can_delete, error_msg = UnitService.can_delete_unit(unit, request.user)
    
    if not can_delete:
        messages.error(request, error_msg)
        return redirect('units:detail', pk=unit.pk)
    
    if request.method == 'POST':
        unit_name = unit.name
        unit.delete()
        messages.success(request, f'Подразделение "{unit_name}" удалено')
        return redirect('units:list')
    
    return render(request, 'units/delete.html', {
        'unit': unit,
        'active_tab': 'units',
        'title': 'Удаление подразделения',
    })