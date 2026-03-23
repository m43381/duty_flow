from django.contrib import admin
from .models import MonthlySchedule, DayPlan, DutyAssignment


@admin.register(MonthlySchedule)
class MonthlyScheduleAdmin(admin.ModelAdmin):
    list_display = ('month', 'name', 'unit', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'month', 'unit')
    search_fields = ('name',)
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('month', 'name', 'status', 'unit')
        }),
        ('Иерархия', {
            'fields': ('parent_schedule',),
        }),
        ('Аудит', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DayPlan)
class DayPlanAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'date', 'duty_type', 'unit', 'status', 'created_at')
    list_filter = ('schedule__month', 'schedule__unit', 'duty_type', 'status')
    search_fields = ('unit__name', 'duty_type__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Расписание', {
            'fields': ('schedule', 'date')
        }),
        ('Назначение', {
            'fields': ('duty_type', 'unit', 'status')
        }),
        ('Иерархия', {
            'fields': ('parent',),
        }),
        ('Аудит', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(DutyAssignment)
class DutyAssignmentAdmin(admin.ModelAdmin):
    list_display = ('day_plan', 'person', 'assigned_by', 'assigned_at')
    list_filter = ('day_plan__schedule__month', 'day_plan__duty_type')
    search_fields = ('person__last_name',)
    readonly_fields = ('assigned_by', 'assigned_at')
    
    fieldsets = (
        ('Назначение', {
            'fields': ('day_plan', 'person')
        }),
        ('Аудит', {
            'fields': ('assigned_by', 'assigned_at'),
            'classes': ('collapse',),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)