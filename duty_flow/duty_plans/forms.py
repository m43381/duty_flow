from django import forms
from .models import MonthlySchedule, DayPlan


class MonthlyScheduleForm(forms.ModelForm):
    """Форма для расписания на месяц"""
    
    class Meta:
        model = MonthlySchedule
        fields = ['month', 'name', 'status', 'parent_schedule']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Например: Июнь 2026'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'parent_schedule': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Поле month создается вручную
        self.fields['month'] = forms.DateField(
            label='Месяц',
            widget=forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'month',
            }),
            required=True,
            help_text='Выберите месяц (например, 2026-06)'
        )
        
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