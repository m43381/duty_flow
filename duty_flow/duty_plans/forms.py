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
        fields = ['month', 'name', 'status', 'parent_schedule']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Название (опционально)'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'parent_schedule': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk and self.instance.month:
            self.initial['month'] = self.instance.month.strftime('%Y-%m')
        
        if self.user and hasattr(self.user, 'profile'):
            from users_app.access_service import AccessService
            access = AccessService(self.user)
            
            parent_units = access.user_unit.get_ancestors()
            self.fields['parent_schedule'].queryset = MonthlySchedule.objects.filter(
                status='published',
                unit__in=parent_units
            )
            self.fields['parent_schedule'].empty_label = "— Корневое расписание —"
            self.fields['parent_schedule'].required = False
    
    def clean_month(self):
        month = self.cleaned_data.get('month')
        if month:
            return month.replace(day=1)
        return month
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.created_by = self.user
            instance.unit = self.user.profile.unit
        if commit:
            instance.save()
        return instance