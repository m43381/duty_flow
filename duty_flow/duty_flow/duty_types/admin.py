from django.contrib import admin
from .models import DutyType

@admin.register(DutyType)
class DutyTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'required_people', 'unit', 'created_by_unit')
    list_filter = ('unit', 'required_people')
    search_fields = ('name', 'description')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'required_people')
        }),
        ('Привязка к подразделениям', {
            'fields': ('unit', 'created_by_unit'),
            'classes': ('wide',),
        }),
    )