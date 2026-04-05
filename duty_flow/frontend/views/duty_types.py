from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction

from duty_types.models import DutyType
from duty_types.forms import DutyTypeForm
from users_app.access_service import AccessService


@login_required
def list(request):
    access = AccessService(request.user)
    user_unit = access.user_unit
    
    # Показываем типы нарядов, созданные этим подразделением
    duty_types = DutyType.objects.filter(created_by_unit=user_unit).order_by('name')
    
    return render(request, 'type/list.html', {
        'items': duty_types,
        'active_tab': 'type',
        'title': 'Мои типы нарядов',
        'can_add': True,
    })


@login_required
def add(request):
    if request.method == 'POST':
        form = DutyTypeForm(request.POST, user=request.user)
        if form.is_valid():
            duty_type = form.save(commit=False, user=request.user)
            duty_type.save()
            messages.success(request, f'Тип наряда "{duty_type.name}" создан')
            return redirect('type:list')
    else:
        form = DutyTypeForm(user=request.user)
    
    return render(request, 'type/form.html', {
        'form': form,
        'active_tab': 'type',
        'title': 'Создание типа наряда',
    })


@login_required
def detail(request, pk):
    duty_type = get_object_or_404(DutyType, pk=pk)
    access = AccessService(request.user)
    
    if duty_type.created_by_unit != access.user_unit:
        messages.error(request, 'Нет доступа')
        return redirect('type:list')
    
    return render(request, 'type/detail.html', {
        'item': duty_type,
        'active_tab': 'type',
        'title': duty_type.name,
    })


@login_required
def edit(request, pk):
    duty_type = get_object_or_404(DutyType, pk=pk)
    access = AccessService(request.user)
    
    if duty_type.created_by_unit != access.user_unit:
        messages.error(request, 'Нет доступа')
        return redirect('type:list')
    
    if request.method == 'POST':
        form = DutyTypeForm(request.POST, instance=duty_type, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тип наряда обновлен')
            return redirect('type:detail', pk=duty_type.pk)
    else:
        form = DutyTypeForm(instance=duty_type, user=request.user)
    
    return render(request, 'type/form.html', {
        'form': form,
        'item': duty_type,
        'active_tab': 'type',
        'title': 'Редактирование',
    })


@login_required
def delete(request, pk):
    duty_type = get_object_or_404(DutyType, pk=pk)
    access = AccessService(request.user)
    
    if duty_type.created_by_unit != access.user_unit:
        messages.error(request, 'Нет доступа')
        return redirect('type:list')
    
    if request.method == 'POST':
        duty_type.delete()
        messages.success(request, 'Тип наряда удален')
        return redirect('type:list')
    
    return render(request, 'type/delete.html', {
        'item': duty_type,
        'active_tab': 'type',
        'title': 'Удаление',
    })