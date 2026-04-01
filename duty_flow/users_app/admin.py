from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline для профиля пользователя в админке пользователя"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fk_name = 'user'  # Явно указываем, какое поле использовать для связи
    fields = ('unit', 'created_by', 'created_at')
    readonly_fields = ('created_at',)


class CustomUserAdmin(UserAdmin):
    """Кастомный админ для пользователя с профилем"""
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'get_unit', 'get_created_by')
    list_filter = ('is_active', 'is_staff', 'profile__unit')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    def get_unit(self, obj):
        """Получить подразделение пользователя"""
        if hasattr(obj, 'profile'):
            return obj.profile.unit.name
        return '-'
    get_unit.short_description = 'Подразделение'
    get_unit.admin_order_field = 'profile__unit__name'
    
    def get_created_by(self, obj):
        """Получить создателя пользователя"""
        if hasattr(obj, 'profile') and obj.profile.created_by:
            return obj.profile.created_by.username
        return '-'
    get_created_by.short_description = 'Создал'
    get_created_by.admin_order_field = 'profile__created_by__username'


# Отменяем регистрацию стандартного UserAdmin и регистрируем кастомный
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# Если нужно отдельно зарегистрировать UserProfile
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Админ для профилей пользователей"""
    list_display = ('user', 'unit', 'created_by', 'created_at')
    list_filter = ('unit', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'unit__name')
    raw_id_fields = ('user', 'created_by')
    readonly_fields = ('created_at',)