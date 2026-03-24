from django import forms
from .models import MonthlySchedule


class MonthlyScheduleForm(forms.ModelForm):
    month = forms.DateField(
        label='Месяц',
        widget=forms.DateInput(attrs={
            'type': 'month',
            'class': 'form-input',
        }),
        input_formats=['%Y-%m'],
        required=True
    )
    
    class Meta:
        model = MonthlySchedule
        fields = ['month', 'name', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Например: Март 2026'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk and self.instance.month:
            self.initial['month'] = self.instance.month.strftime('%Y-%m')
    
    def clean_month(self):
        month = self.cleaned_data.get('month')
        if month:
            return month.replace(day=1)
        return month
    
    def clean(self):
        cleaned_data = super().clean()
        month = cleaned_data.get('month')
        
        # Проверка уникальности: одно расписание на месяц для подразделения
        if self.user and month:
            existing = MonthlySchedule.objects.filter(
                month=month,
                unit=self.user.profile.unit
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise forms.ValidationError(
                    f'Расписание на {month.strftime("%B %Y")} уже существует.'
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.created_by = self.user
            instance.unit = self.user.profile.unit
        if commit:
            instance.save()
        return instance