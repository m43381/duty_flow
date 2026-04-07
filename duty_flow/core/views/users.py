from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from users_app.forms import UserCreateForm, UserEditForm, UserChangePasswordForm
from core.services.user_service import UserService
from access_control.services import AccessManager


def apply_user_access_to_form(form, access_manager, action: str):
    visible_fields = set(access_manager.visible_user_fields(action))
    editable_fields = set(access_manager.editable_user_fields(action))

    # Эти поля есть только у формы создания пользователя
    technical_fields = {"password", "password_confirm"}

    for field_name in list(form.fields.keys()):
        # Парольные поля не фильтруем через ACL полей
        if field_name in technical_fields:
            continue

        if field_name not in visible_fields:
            form.fields.pop(field_name, None)
            continue

        if field_name not in editable_fields:
            form.fields[field_name].disabled = True

    # В твоей create-форме unit — это ChoiceField, не ModelChoiceField
    # поэтому меняем choices, а не queryset
    if "unit" in form.fields:
        if action == "create":
            units = access_manager.allowed_units_for_user_creation()
        elif action == "update":
            units = access_manager.allowed_units_for_user_update()
        else:
            units = None

        if units is not None:
            form.fields["unit"].choices = [
                (unit.id, f"{unit.name} ({unit.unit_type.name})")
                for unit in units
            ]


@login_required
def user_list(request):
    """Список пользователей"""
    users = UserService.get_visible_users(request.user)

    search_query = request.GET.get("q", "").strip()
    users = UserService.search_users(users, search_query)
    users = UserService.enrich_users_with_permissions(users, request.user)

    context = {
        "users": users,
        "search_query": search_query,
        "can_add": UserService.can_create_user(request.user),
        "active_tab": "users",
        "page_title": "Пользователи",
        "page_subtitle": "Список пользователей",
    }
    return render(request, "app/users/list.html", context)


@login_required
def user_add(request):
    """Создание пользователя"""
    access = AccessManager(request.user)

    if not access.can_user("create"):
        messages.error(request, "У вас нет прав на создание пользователей")
        return redirect("users:list")

    if request.method == "POST":
        form = UserCreateForm(request.POST, user=request.user)
        apply_user_access_to_form(form, access, "create")

        if form.is_valid():
            user_obj = UserService.create_user(form.cleaned_data, request.user)
            messages.success(request, f'Пользователь "{user_obj.username}" создан')
            return redirect("users:detail", pk=user_obj.pk)
    else:
        form = UserCreateForm(user=request.user)
        apply_user_access_to_form(form, access, "create")

    return render(request, "app/users/form.html", {
        "form": form,
        "active_tab": "users",
        "page_title": "Пользователи",
        "page_subtitle": "Создание пользователя",
        "title": "Создать пользователя",
    })


@login_required
def user_detail(request, pk):
    """Просмотр пользователя"""
    user_obj = get_object_or_404(
        User.objects.select_related("profile", "profile__unit", "profile__unit__unit_type"),
        pk=pk
    )
    access = AccessManager(request.user)

    if not access.can_user("view", user_obj):
        messages.error(request, "У вас нет прав на просмотр этого пользователя")
        return redirect("users:list")

    return render(request, "app/users/detail.html", {
        "user_obj": user_obj,
        "can_edit": access.can_user("update", user_obj),
        "can_delete": access.can_user("delete", user_obj),
        "can_change_password": access.can_user("change_password", user_obj),
        "visible_fields": access.visible_user_fields("view"),
        "active_tab": "users",
        "page_title": "Пользователи",
        "page_subtitle": "Карточка пользователя",
        "title": user_obj.get_full_name() or user_obj.username,
    })


@login_required
def user_edit(request, pk):
    """Редактирование пользователя"""
    user_obj = get_object_or_404(
        User.objects.select_related("profile", "profile__unit", "profile__unit__unit_type"),
        pk=pk
    )
    access = AccessManager(request.user)

    if not access.can_user("update", user_obj):
        messages.error(request, "У вас нет прав на редактирование этого пользователя")
        return redirect("users:list")

    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user_obj, user=request.user)
        apply_user_access_to_form(form, access, "update")

        if form.is_valid():
            UserService.update_user(user_obj, form.cleaned_data)
            messages.success(request, f'Пользователь "{user_obj.username}" обновлен')
            return redirect("users:detail", pk=user_obj.pk)
    else:
        form = UserEditForm(instance=user_obj, user=request.user)
        apply_user_access_to_form(form, access, "update")

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
    access = AccessManager(request.user)

    if not access.can_user("delete", user_obj):
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
    access = AccessManager(request.user)

    if not access.can_user("change_password", user_obj):
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