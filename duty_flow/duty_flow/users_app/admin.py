from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = "Профиль"
    verbose_name_plural = "Профиль"
    
    fieldsets = (
        ('Информация о пользователе', {
            'fields': ('unit', 'access_level')
        }),
    )

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_unit', 'get_access_level')
    list_select_related = ('profile', 'profile__unit')
    
    fieldsets = (
        ('Логин и пароль', {
            'fields': ('username', 'password')
        }),
        ('Персональные данные', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('wide',),
        }),
        ('Важные даты', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )
    
    add_fieldsets = (
        ('Создание нового пользователя', {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )
    
    def get_unit(self, instance):
        if hasattr(instance, 'profile') and instance.profile.unit:
            return instance.profile.unit.name
        return '-'
    get_unit.short_description = 'Подразделение'
    
    def get_access_level(self, instance):
        if hasattr(instance, 'profile') and instance.profile.access_level:
            return instance.profile.get_access_level_display()
        return '-'
    get_access_level.short_description = 'Уровень доступа'

# Перерегистрируем модель User
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)