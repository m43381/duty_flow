from django import forms
from .models import MonthlySchedule, DayPlan


class MonthlyScheduleForm(forms.ModelForm):
    """Форма для расписания на месяц"""
    
    month = forms.DateField(
        label='Месяц',
        widget=forms.DateInput(attrs={
            'class': 'form-input',
            'type': 'month',
        }),
        required=True,
        input_formats=['%Y-%m']
    )
    
    class Meta:
        model = MonthlySchedule
        fields = ['month', 'name', 'status', 'parent_schedule']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Например: Март 2026'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'parent_schedule': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk and self.instance.month:
            self.initial['month'] = self.instance.month.strftime('%Y-%m')
        
        if self.user:
            from users_app.access_service import AccessService
            access = AccessService(self.user)
            user_unit = access.user_unit
            
            # Доступные родительские расписания: опубликованные, вышестоящие подразделения
            parent_units = user_unit.get_ancestors()
            self.fields['parent_schedule'].queryset = MonthlySchedule.objects.filter(
                status='published',
                created_by__profile__unit__in=parent_units
            ).order_by('-month')
            self.fields['parent_schedule'].required = False
            self.fields['parent_schedule'].empty_label = "— Корневое расписание —"
    
    def clean_month(self):
        month = self.cleaned_data.get('month')
        if month:
            month = month.replace(day=1)
        return month
    
    def clean(self):
        cleaned_data = super().clean()
        month = cleaned_data.get('month')
        parent = cleaned_data.get('parent_schedule')
        
        if parent and month and parent.month != month:
            raise forms.ValidationError(
                f'Родительское расписание "{parent}" создано на другой месяц. '
                f'Выберите расписание за тот же месяц или оставьте поле пустым.'
            )
        
        return cleaned_data


class DayPlanForm(forms.ModelForm):
    """Форма для плана на день (используется в таблице)"""
    
    class Meta:
        model = DayPlan
        fields = ['date', 'duty_type', 'unit', 'execution_type']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'duty_type': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'execution_type': forms.Select(attrs={'class': 'form-select'}),
        }