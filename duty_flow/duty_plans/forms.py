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
        help_text='Выберите месяц из календаря (формат: ГГГГ-ММ)',
        input_formats=['%Y-%m']
    )
    
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
        
        # Если есть начальное значение и это date, преобразуем для отображения
        if self.instance and self.instance.pk and self.instance.month:
            self.initial['month'] = self.instance.month.strftime('%Y-%m')
        
        self.fields['parent_schedule'].queryset = MonthlySchedule.objects.filter(
            status='published'
        ).order_by('-month')
        self.fields['parent_schedule'].required = False
        self.fields['parent_schedule'].empty_label = "— Корневое расписание —"
    
    def clean_month(self):
        month = self.cleaned_data.get('month')
        if month:
            # Приводим к первому числу месяца
            month = month.replace(day=1)
        return month


class DayPlanForm(forms.ModelForm):
    """Форма для плана на день (используется в таблице)"""
    
    class Meta:
        model = DayPlan
        fields = ['date', 'unit', 'duty_type']