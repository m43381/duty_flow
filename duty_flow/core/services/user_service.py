"""
Сервис для работы с пользователями
"""
from django.db import models
from django.contrib.auth.models import User

from users_app.access_service import AccessService
from users_app.models import UserProfile
from access_control.services import AccessManager


class UserService:
    """Сервис для работы с пользователями"""

    @staticmethod
    def get_visible_users(user):
        """
        Возвращает queryset пользователей с учетом новой системы доступа.
        Если правил нет, AccessManager сам использует legacy fallback.
        """
        access = AccessManager(user)
        qs = (
            User.objects
            .select_related("profile", "profile__unit", "profile__unit__unit_type")
            .all()
        )
        return access.scope_users(qs)

    @staticmethod
    def search_users(users_qs, search_query):
        """Поиск пользователей по различным полям"""
        if search_query:
            return users_qs.filter(
                models.Q(username__icontains=search_query) |
                models.Q(first_name__icontains=search_query) |
                models.Q(last_name__icontains=search_query) |
                models.Q(email__icontains=search_query)
            )
        return users_qs

    @staticmethod
    def get_available_units_for_creation(user):
        access = AccessManager(user)
        return list(access.allowed_units_for_user_creation())

    @staticmethod
    def can_create_user(user):
        access = AccessManager(user)
        return access.can_user("create")

    @staticmethod
    def enrich_users_with_permissions(users_qs, current_user):
        access = AccessManager(current_user)
        for user in users_qs:
            user.can_edit = access.can_user("update", user)
            user.can_delete = access.can_user("delete", user)
            user.can_change_password = access.can_user("change_password", user)
        return users_qs

    @staticmethod
    def get_user_with_profile(pk):
        return User.objects.select_related("profile", "profile__unit", "profile__unit__unit_type").get(pk=pk)

    @staticmethod
    def create_user(form_data, created_by):
        user = User.objects.create_user(
            username=form_data["username"],
            password=form_data["password"],
            email=form_data.get("email", ""),
            first_name=form_data.get("first_name", ""),
            last_name=form_data.get("last_name", "")
        )

        UserProfile.objects.create(
            user=user,
            unit_id=form_data["unit"],
            created_by=created_by
        )

        return user

    @staticmethod
    def update_user(user, form_data):
        user.username = form_data["username"]
        user.email = form_data.get("email", "")
        user.first_name = form_data.get("first_name", "")
        user.last_name = form_data.get("last_name", "")
        user.save()

        unit_id = form_data.get("unit")
        if unit_id and str(user.profile.unit_id) != str(unit_id):
            user.profile.unit_id = unit_id
            user.profile.save()

        return user

    @staticmethod
    def change_password(user, new_password):
        user.set_password(new_password)
        user.save()

    @staticmethod
    def delete_user(user):
        user.delete()