from django.contrib import admin
from .models import Person, Exemption, DutyClearance, DutyType

class ExemptionInline(admin.TabularInline):
    model = Exemption
    extra = 0
    verbose_name = "Освобождение"
    verbose_name_plural = "Освобождения"

class DutyClearanceInline(admin.TabularInline):
    model = DutyClearance
    extra = 0
    verbose_name = "Допуск"
    verbose_name_plural = "Допуски"

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'middle_name', 'rank', 'unit')
    list_filter = ('rank', 'unit')
    search_fields = ('last_name', 'first_name', 'middle_name')
    
    fieldsets = (
        ('ФИО', {
            'fields': ('last_name', 'first_name', 'middle_name')
        }),
        ('Служебная информация', {
            'fields': ('rank', 'unit'),
            'classes': ('wide',),
        }),
    )
    
    inlines = [ExemptionInline, DutyClearanceInline]

@admin.register(Exemption)
class ExemptionAdmin(admin.ModelAdmin):
    list_display = ('person', 'get_reason_display', 'date_from', 'date_to')
    list_filter = ('reason', 'date_from')
    search_fields = ('person__last_name', 'comment')
    
    fieldsets = (
        ('Сотрудник', {
            'fields': ('person',)
        }),
        ('Период освобождения', {
            'fields': ('reason', 'date_from', 'date_to', 'comment')
        }),
    )

@admin.register(DutyClearance)
class DutyClearanceAdmin(admin.ModelAdmin):
    list_display = ('person', 'duty_type')
    list_filter = ('duty_type',)
    search_fields = ('person__last_name',)
    
    fieldsets = (
        ('Информация о допуске', {
            'fields': ('person', 'duty_type')
        }),
    )