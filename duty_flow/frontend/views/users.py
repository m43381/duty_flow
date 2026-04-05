from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db import models

from users_app.forms import UserCreateForm, UserEditForm, UserChangePasswordForm
from users_app.access_service import AccessService
from units.models import Unit


@login_required
def list_view(request):
    """Список пользователей"""
    access = AccessService(request.user)
    
    # Получаем видимых пользователей
    users = access.get_visible_users()
    
    # Поиск
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            models.Q(username__icontains=search_query) |
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query) |
            models.Q(email__icontains=search_query)
        )
    
    # Проверка на создание - можно создать в своем или прямом дочернем
    can_create = False
    for unit in [access.user_unit] + list(access.user_unit.children.all()):
        if access.can_create_user_for_unit(unit):
            can_create = True
            break
    
    # Для каждой записи в шаблоне будем проверять права
    # Добавляем объект access в контекст для использования в шаблоне
    for user in users:
        # Добавляем атрибуты для проверки прав в шаблоне
        user.can_edit = access.can_edit_user(user)
        user.can_delete = access.can_delete_user(user)
        user.can_change_password = access.can_change_password(user)
    
    return render(request, 'users/list.html', {
        'users': users,
        'can_create': can_create,
        'search_query': search_query,
        'active_tab': 'users',
        'title': 'Пользователи',
        'user_access': access,  # Передаем объект access в шаблон
    })


@login_required
def create_view(request):
    """Создание пользователя"""
    access = AccessService(request.user)
    
    # Проверка: есть ли куда создавать
    available_units = []
    
    # Свое подразделение
    available_units.append(access.user_unit)
    
    # Прямые дочерние
    for child in access.user_unit.children.all():
        available_units.append(child)
    
    if not available_units:
        messages.error(request, 'У вас нет прав на создание пользователей')
        return redirect('users:list')
    
    if request.method == 'POST':
        form = UserCreateForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, f'Пользователь "{user.username}" создан')
                return redirect('users:detail', pk=user.pk)
            except IntegrityError as e:
                messages.error(request, f'Ошибка: {str(e)}')
    else:
        form = UserCreateForm(user=request.user)
        
        # Если есть предустановленное подразделение из GET
        unit_id = request.GET.get('unit')
        if unit_id:
            try:
                unit = Unit.objects.get(pk=unit_id)
                # Проверяем, что подразделение доступно для создания
                if unit in available_units:
                    form.initial['unit'] = unit.id
            except Unit.DoesNotExist:
                pass
    
    return render(request, 'users/create.html', {
        'form': form,
        'active_tab': 'users',
        'title': 'Создание пользователя',
        'available_units': available_units,
    })


@login_required
def detail_view(request, pk):
    """Просмотр пользователя"""
    user_obj = get_object_or_404(User.objects.select_related('profile'), pk=pk)
    access = AccessService(request.user)
    
    # Проверка доступа к просмотру
    if not access.can_view_unit(user_obj.profile.unit):
        messages.error(request, 'У вас нет доступа к этому пользователю')
        return redirect('users:list')
    
    can_edit = access.can_edit_user(user_obj)
    can_delete = access.can_delete_user(user_obj)
    can_change_password = access.can_change_password(user_obj)
    
    return render(request, 'users/detail.html', {
        'user_obj': user_obj,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'can_change_password': can_change_password,
        'active_tab': 'users',
        'title': f'Пользователь: {user_obj.get_full_name() or user_obj.username}',
    })


@login_required
def edit_view(request, pk):
    """Редактирование пользователя"""
    user_obj = get_object_or_404(User, pk=pk)
    access = AccessService(request.user)
    
    # Проверка прав на редактирование
    if not access.can_edit_user(user_obj):
        messages.error(request, 'У вас нет прав на редактирование этого пользователя')
        return redirect('users:list')
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_obj, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Пользователь "{user_obj.username}" обновлен')
            return redirect('users:detail', pk=user_obj.pk)
    else:
        form = UserEditForm(instance=user_obj, user=request.user)
    
    return render(request, 'users/edit.html', {
        'form': form,
        'user_obj': user_obj,
        'active_tab': 'users',
        'title': f'Редактирование: {user_obj.get_full_name() or user_obj.username}',
    })


@login_required
def delete_view(request, pk):
    """Удаление пользователя"""
    user_obj = get_object_or_404(User, pk=pk)
    access = AccessService(request.user)
    
    # Проверка прав на удаление
    if not access.can_delete_user(user_obj):
        messages.error(request, 'У вас нет прав на удаление этого пользователя')
        return redirect('users:list')
    
    if request.method == 'POST':
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f'Пользователь "{username}" удален')
        return redirect('users:list')
    
    return render(request, 'users/delete.html', {
        'user_obj': user_obj,
        'active_tab': 'users',
        'title': f'Удаление пользователя: {user_obj.get_full_name() or user_obj.username}',
    })


@login_required
def change_password_view(request, pk):
    """Смена пароля пользователя"""
    user_obj = get_object_or_404(User, pk=pk)
    access = AccessService(request.user)
    
    # Проверка прав на смену пароля
    if not access.can_change_password(user_obj):
        messages.error(request, 'У вас нет прав на смену пароля этого пользователя')
        return redirect('users:list')
    
    if request.method == 'POST':
        form = UserChangePasswordForm(request.POST)
        if form.is_valid():
            user_obj.set_password(form.cleaned_data['new_password'])
            user_obj.save()
            messages.success(request, f'Пароль пользователя "{user_obj.username}" успешно изменен')
            return redirect('users:detail', pk=user_obj.pk)
    else:
        form = UserChangePasswordForm()
    
    return render(request, 'users/change_password.html', {
        'form': form,
        'user_obj': user_obj,
        'active_tab': 'users',
        'title': f'Смена пароля: {user_obj.get_full_name() or user_obj.username}',
    })