from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from users_app.forms import UserCreateForm, UserEditForm, UserChangePasswordForm
from users_app.access_service import AccessService
from core.services.user_service import UserService


@login_required
def user_list(request):
    """Список пользователей"""
    users = UserService.get_visible_users(request.user)

    search_query = request.GET.get("q", "").strip()
    if search_query:
        users = UserService.search_users(users, search_query)

    users = UserService.enrich_users_with_permissions(users, request.user)
    can_add = UserService.can_create_user(request.user)

    return render(request, "app/users/list.html", {
        "users": users,
        "can_add": can_add,
        "search_query": search_query,
        "active_tab": "users",
        "page_title": "Пользователи",
        "page_subtitle": "Список учетных записей",
    })


@login_required
def user_create(request):
    """Создание пользователя"""
    available_units = UserService.get_available_units_for_creation(request.user)

    if not available_units:
        messages.error(request, "У вас нет прав на создание пользователей")
        return redirect("users:list")

    if request.method == "POST":
        form = UserCreateForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                user_obj = UserService.create_user(form.cleaned_data, request.user)
                messages.success(request, f'Пользователь "{user_obj.username}" создан')
                return redirect("users:detail", pk=user_obj.pk)
            except Exception as e:
                messages.error(request, f"Ошибка: {str(e)}")
    else:
        form = UserCreateForm(user=request.user)

        unit_id = request.GET.get("unit")
        if unit_id and available_units:
            try:
                from units.models import Unit
                unit = Unit.objects.get(pk=unit_id)
                if unit in available_units:
                    form.initial["unit"] = unit.id
            except Exception:
                pass

    return render(request, "app/users/form.html", {
        "form": form,
        "user_obj": None,
        "active_tab": "users",
        "page_title": "Пользователи",
        "page_subtitle": "Создание пользователя",
        "title": "Создать пользователя",
    })


@login_required
def user_detail(request, pk):
    try:
        user_obj = UserService.get_user_with_profile(pk)
    except User.DoesNotExist:
        messages.error(request, "Пользователь не найден")
        return redirect("users:list")

    access = AccessService(request.user)

    if not access.can_view_unit(user_obj.profile.unit):
        messages.error(request, "У вас нет доступа к этому пользователю")
        return redirect("users:list")

    can_edit = access.can_edit_user(user_obj)
    can_delete = access.can_delete_user(user_obj)
    can_change_password = access.can_change_password(user_obj)

    return render(request, "app/users/detail.html", {
        "user_obj": user_obj,
        "can_edit": can_edit,
        "can_delete": can_delete,
        "can_change_password": can_change_password,
        "active_tab": "users",
        "page_title": "Пользователи",
        "page_subtitle": "Карточка пользователя",
        "title": f'Пользователь: {user_obj.get_full_name() or user_obj.username}',
    })


@login_required
def user_edit(request, pk):
    """Редактирование пользователя"""
    user_obj = get_object_or_404(User, pk=pk)
    access = AccessService(request.user)

    if not access.can_edit_user(user_obj):
        messages.error(request, "У вас нет прав на редактирование этого пользователя")
        return redirect("users:list")

    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user_obj, user=request.user)
        if form.is_valid():
            UserService.update_user(user_obj, form.cleaned_data)
            messages.success(request, f'Пользователь "{user_obj.username}" обновлен')
            return redirect("users:detail", pk=user_obj.pk)
    else:
        form = UserEditForm(instance=user_obj, user=request.user)

    return render(request, "app/users/form.html", {
        "form": form,
        "user_obj": user_obj,
        "active_tab": "users",
        "page_title": "Пользователи",
        "page_subtitle": "Редактирование пользователя",
        "title": f'Редактировать: {user_obj.get_full_name() or user_obj.username}',
    })


@login_required
def user_delete(request, pk):
    """Удаление пользователя"""
    user_obj = get_object_or_404(User, pk=pk)
    access = AccessService(request.user)

    if not access.can_delete_user(user_obj):
        messages.error(request, "У вас нет прав на удаление этого пользователя")
        return redirect("users:list")

    if request.method == "POST":
        username = user_obj.username
        UserService.delete_user(user_obj)
        messages.success(request, f'Пользователь "{username}" удален')
        return redirect("users:list")

    return render(request, "app/users/delete.html", {
        "user_obj": user_obj,
        "active_tab": "users",
        "page_title": "Пользователи",
        "page_subtitle": "Удаление пользователя",
        "title": f'Удаление пользователя: {user_obj.get_full_name() or user_obj.username}',
    })


@login_required
def user_change_password(request, pk):
    """Смена пароля пользователя"""
    user_obj = get_object_or_404(User, pk=pk)
    access = AccessService(request.user)

    if not access.can_change_password(user_obj):
        messages.error(request, "У вас нет прав на смену пароля этого пользователя")
        return redirect("users:list")

    if request.method == "POST":
        form = UserChangePasswordForm(request.POST)
        if form.is_valid():
            UserService.change_password(user_obj, form.cleaned_data["new_password"])
            messages.success(request, f'Пароль пользователя "{user_obj.username}" успешно изменен')
            return redirect("users:detail", pk=user_obj.pk)
    else:
        form = UserChangePasswordForm()

    return render(request, "app/users/change_password.html", {
        "form": form,
        "user_obj": user_obj,
        "active_tab": "users",
        "page_title": "Пользователи",
        "page_subtitle": "Смена пароля пользователя",
        "title": f'Смена пароля: {user_obj.get_full_name() or user_obj.username}',
    })