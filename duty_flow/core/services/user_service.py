"""
Сервис для работы с пользователями
"""
from django.db import models
from django.contrib.auth.models import User
from users_app.access_service import AccessService


class UserService:
    """Сервис для работы с пользователями"""
    
    @staticmethod
    def get_visible_users(user):
        """Возвращает queryset пользователей, доступных для просмотра"""
        access = AccessService(user)
        return access.get_visible_users()
    
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
        """Возвращает список подразделений, в которых можно создавать пользователей"""
        access = AccessService(user)
        available_units = [access.user_unit]
        available_units.extend(list(access.user_unit.children.all()))
        return available_units
    
    @staticmethod
    def can_create_user(user):
        """Проверяет, может ли пользователь создавать новых пользователей"""
        access = AccessService(user)
        for unit in [access.user_unit] + list(access.user_unit.children.all()):
            if access.can_create_user_for_unit(unit):
                return True
        return False
    
    @staticmethod
    def enrich_users_with_permissions(users_qs, current_user):
        """Добавляет каждому пользователю атрибуты с правами доступа"""
        access = AccessService(current_user)
        for user in users_qs:
            user.can_edit = access.can_edit_user(user)
            user.can_delete = access.can_delete_user(user)
            user.can_change_password = access.can_change_password(user)
        return users_qs
    
    @staticmethod
    def get_user_with_profile(pk):
        """Возвращает пользователя с предзагруженным профилем"""
        return User.objects.select_related('profile').get(pk=pk)
    
    @staticmethod
    def create_user(form_data, created_by):
        """Создаёт нового пользователя"""
        from users_app.models import UserProfile
        
        user = User.objects.create_user(
            username=form_data['username'],
            password=form_data['password1'],
            email=form_data.get('email', ''),
            first_name=form_data.get('first_name', ''),
            last_name=form_data.get('last_name', '')
        )
        
        UserProfile.objects.create(
            user=user,
            unit=form_data['unit'],
            created_by=created_by
        )
        
        return user
    
    @staticmethod
    def update_user(user, form_data):
        """Обновляет данные пользователя"""
        user.username = form_data['username']
        user.email = form_data.get('email', '')
        user.first_name = form_data.get('first_name', '')
        user.last_name = form_data.get('last_name', '')
        user.save()
        
        # Обновляем подразделение в профиле
        if 'unit' in form_data and user.profile.unit != form_data['unit']:
            user.profile.unit = form_data['unit']
            user.profile.save()
        
        return user
    
    @staticmethod
    def change_password(user, new_password):
        """Меняет пароль пользователя"""
        user.set_password(new_password)
        user.save()
    
    @staticmethod
    def delete_user(user):
        """Удаляет пользователя"""
        user.delete()