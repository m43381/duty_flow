from django.contrib import admin
from .models import Unit, UnitType

@admin.register(UnitType)
class UnitTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'level', 'can_have_children')
    list_filter = ('level', 'can_have_children')
    search_fields = ('name', 'slug')
    list_editable = ('level', 'can_have_children')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug')
        }),
        ('Иерархия', {
            'fields': ('level', 'can_have_children'),
            'description': 'level: 0 - самый высокий уровень (академия), 1 - факультет, 2 - кафедра и т.д.'
        }),
    )

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit_type', 'parent', 'get_level')
    list_filter = ('unit_type', 'unit_type__level')
    search_fields = ('name',)
    raw_id_fields = ('parent',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'unit_type')
        }),
        ('Иерархия', {
            'fields': ('parent',),
            'description': 'Выберите вышестоящее подразделение (если есть)'
        }),
    )
    
    def get_level(self, obj):
        return obj.unit_type.level
    get_level.short_description = 'Уровень'
    get_level.admin_order_field = 'unit_type__level'