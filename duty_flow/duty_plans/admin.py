from django.contrib import admin
from .models import DutyPlan, DutyAssignment

class DutyAssignmentInline(admin.TabularInline):
    model = DutyAssignment
    extra = 1
    verbose_name = "Назначение"
    verbose_name_plural = "Назначения"

@admin.register(DutyPlan)
class DutyPlanAdmin(admin.ModelAdmin):
    list_display = ('date', 'unit', 'duty_type', 'assignments_count')
    list_filter = ('date', 'unit', 'duty_type')
    search_fields = ('unit__name', 'duty_type__name')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('date', 'unit', 'duty_type')
        }),
    )
    
    inlines = [DutyAssignmentInline]
    
    def assignments_count(self, obj):
        return obj.assignments.count()
    assignments_count.short_description = 'Количество назначений'

@admin.register(DutyAssignment)
class DutyAssignmentAdmin(admin.ModelAdmin):
    list_display = ('plan', 'person', 'get_date', 'get_unit')
    list_filter = ('plan__date', 'plan__unit', 'plan__duty_type')
    search_fields = ('person__last_name', 'person__first_name', 'plan__unit__name')
    
    fieldsets = (
        ('Назначение', {
            'fields': ('plan', 'person')
        }),
    )
    
    def get_date(self, obj):
        return obj.plan.date
    get_date.short_description = 'Дата'
    get_date.admin_order_field = 'plan__date'
    
    def get_unit(self, obj):
        return obj.plan.unit
    get_unit.short_description = 'Подразделение'
    get_unit.admin_order_field = 'plan__unit'