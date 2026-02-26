from django.contrib import admin
from .models import Unit, UnitType

@admin.register(UnitType)
class UnitTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    list_filter = ('name',)
    
    class Meta:
        verbose_name = "Тип подразделения"
        verbose_name_plural = "Типы подразделений"

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit_type', 'parent')
    list_filter = ('unit_type',)
    search_fields = ('name',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'unit_type')
        }),
        ('Иерархия', {
            'fields': ('parent',),
            'classes': ('wide',),
        }),
    )