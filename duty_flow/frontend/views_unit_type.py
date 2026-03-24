from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction

from units.models import UnitType
from units.forms import UnitTypeForm
from users_app.access_service import AccessService


@login_required
def list(request):
    """Список типов подразделений (только для академии)"""
    access = AccessService(request.user)
    
    # Проверка прав: только академия
    if access.user_level != 0:
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
def add(request):
    """Создание типа подразделения"""
    access = AccessService(request.user)
    
    if access.user_level != 0:
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
def detail(request, pk):
    """Просмотр типа подразделения"""
    access = AccessService(request.user)
    
    if access.user_level != 0:
        messages.error(request, 'Доступ только для администраторов')
        return redirect('dashboard')
    
    unit_type = get_object_or_404(UnitType, pk=pk)
    
    # Статистика использования
    units_count = unit_type.units.count()
    users_count = sum(u.users.count() for u in unit_type.units.all())
    
    return render(request, 'unit_type/detail.html', {
        'item': unit_type,
        'units_count': units_count,
        'users_count': users_count,
        'active_tab': 'unit_type',
        'title': unit_type.name,
    })


@login_required
def edit(request, pk):
    """Редактирование типа подразделения"""
    access = AccessService(request.user)
    
    if access.user_level != 0:
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
def delete(request, pk):
    """Удаление типа подразделения"""
    access = AccessService(request.user)
    
    if access.user_level != 0:
        messages.error(request, 'Доступ только для администраторов')
        return redirect('dashboard')
    
    unit_type = get_object_or_404(UnitType, pk=pk)
    
    # Проверка использования
    units_count = unit_type.units.count()
    if units_count > 0:
        messages.error(
            request,
            f'Нельзя удалить тип "{unit_type.name}", так как существуют '
            f'подразделения этого типа ({units_count} шт.). '
            f'Сначала удалите или измените тип у подразделений.'
        )
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