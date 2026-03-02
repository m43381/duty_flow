from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = "Профиль"
    verbose_name_plural = "Профили"
    
    fields = ('unit',)  # только unit, без access_level

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_unit', 'get_unit_type')
    list_select_related = ('profile', 'profile__unit', 'profile__unit__unit_type')
    
    fieldsets = (
        ('Логин и пароль', {
            'fields': ('username', 'password')
        }),
        ('Персональные данные', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
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
    
    def get_unit_type(self, instance):
        if hasattr(instance, 'profile') and instance.profile.unit:
            return instance.profile.unit.unit_type.name
        return '-'
    get_unit_type.short_description = 'Тип подразделения'

# Перерегистрируем модель User
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)