from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from units.models import UnitType
from units.forms import UnitTypeForm
from frontend.services.unit_service import UnitTypeService


@login_required
def unit_type_list(request):
    """Список типов подразделений (только для академии)"""
    if not UnitTypeService.can_manage(request.user):
        messages.error(request, 'Доступ только для администраторов')
        return redirect('dashboard')
    
    unit_types = UnitType.objects.all().order_by('level', 'name')
    
    return render(request, 'unit_type/list.html', {
        'items': unit_types,
        'active_tab': 'unit_type',
        'title': 'Типы подразделений',
        'can_add': True,
    })


@login_required
def unit_type_add(request):
    """Создание типа подразделения"""
    if not UnitTypeService.can_manage(request.user):
        messages.error(request, 'Доступ только для администраторов')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UnitTypeForm(request.POST)
        if form.is_valid():
            unit_type = form.save()
            messages.success(request, f'Тип "{unit_type.name}" создан')
            return redirect('unit_type:list')
    else:
        form = UnitTypeForm()
    
    return render(request, 'unit_type/form.html', {
        'form': form,
        'active_tab': 'unit_type',
        'title': 'Создание типа подразделения',
    })


@login_required
def unit_type_detail(request, pk):
    """Просмотр типа подразделения"""
    if not UnitTypeService.can_manage(request.user):
        messages.error(request, 'Доступ только для администраторов')
        return redirect('dashboard')
    
    unit_type = get_object_or_404(UnitType, pk=pk)
    units_count, users_count = UnitTypeService.get_usage_stats(unit_type)
    
    return render(request, 'unit_type/detail.html', {
        'item': unit_type,
        'units_count': units_count,
        'users_count': users_count,
        'active_tab': 'unit_type',
        'title': unit_type.name,
    })


@login_required
def unit_type_edit(request, pk):
    """Редактирование типа подразделения"""
    if not UnitTypeService.can_manage(request.user):
        messages.error(request, 'Доступ только для администраторов')
        return redirect('dashboard')
    
    unit_type = get_object_or_404(UnitType, pk=pk)
    
    if request.method == 'POST':
        form = UnitTypeForm(request.POST, instance=unit_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'Тип "{unit_type.name}" обновлен')
            return redirect('unit_type:detail', pk=unit_type.pk)
    else:
        form = UnitTypeForm(instance=unit_type)
    
    return render(request, 'unit_type/form.html', {
        'form': form,
        'item': unit_type,
        'active_tab': 'unit_type',
        'title': 'Редактирование типа подразделения',
    })


@login_required
def unit_type_delete(request, pk):
    """Удаление типа подразделения"""
    if not UnitTypeService.can_manage(request.user):
        messages.error(request, 'Доступ только для администраторов')
        return redirect('dashboard')
    
    unit_type = get_object_or_404(UnitType, pk=pk)
    
    can_delete, error_msg = UnitTypeService.can_delete_type(unit_type)
    if not can_delete:
        messages.error(request, error_msg)
        return redirect('unit_type:detail', pk=unit_type.pk)
    
    if request.method == 'POST':
        unit_type.delete()
        messages.success(request, f'Тип "{unit_type.name}" удален')
        return redirect('unit_type:list')
    
    return render(request, 'unit_type/delete.html', {
        'item': unit_type,
        'active_tab': 'unit_type',
        'title': 'Удаление типа подразделения',
    })