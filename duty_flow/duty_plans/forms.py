from django import forms
from .models import MonthlySchedule, DayPlan


class MonthlyScheduleForm(forms.ModelForm):
    """Форма для расписания на месяц"""
    
    class Meta:
        model = MonthlySchedule
        fields = ['month', 'name', 'status', 'unit', 'parent_schedule']
        widgets = {
            'month': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'month',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Например: Март 2026'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'parent_schedule': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            from users_app.access_service import AccessService
            access = AccessService(self.user)
            self.fields['unit'].queryset = access.get_visible_units()
        
        self.fields['parent_schedule'].queryset = MonthlySchedule.objects.filter(
            status='published'
        ).order_by('-month')
        self.fields['parent_schedule'].required = False
        self.fields['parent_schedule'].empty_label = "— Корневое расписание —"
    
    def clean_month(self):
        month = self.cleaned_data.get('month')
        if month:
            month = month.replace(day=1)
        return month


class DayPlanForm(forms.ModelForm):
    """Форма для плана на день (используется в таблице)"""
    
    class Meta:
        model = DayPlan
        fields = ['date', 'unit', 'duty_type']