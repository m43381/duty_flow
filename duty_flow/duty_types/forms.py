from django import forms
from .models import DutyType
from units.models import Unit


class DutyTypeForm(forms.ModelForm):
    class Meta:
        model = DutyType
        fields = ['name', 'description', 'required_people', 'unit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Название наряда'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'required_people': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and hasattr(user, 'profile'):
            from users_app.access_service import AccessService
            access = AccessService(user)
            
            # Доступные подразделения для закрепления (опционально)
            self.fields['unit'].queryset = access.get_visible_units()
            self.fields['unit'].label_from_instance = lambda obj: f"{obj.name} ({obj.unit_type.name})"
            self.fields['unit'].required = False
            self.fields['unit'].empty_label = "— Не закреплено —"
    
    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        if user:
            instance.created_by_unit = user.profile.unit
        if commit:
            instance.save()
        return instance