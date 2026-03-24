from django import forms
from .models import UnitType


class UnitTypeForm(forms.ModelForm):
    class Meta:
        model = UnitType
        fields = ['name', 'slug', 'level', 'can_have_children']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Например: Факультет'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'faculty'
            }),
            'level': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 0,
                'step': 1
            }),
            'can_have_children': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
        help_texts = {
            'slug': 'Уникальный идентификатор (только латиница, цифры, дефис)',
            'level': '0 — самый высокий уровень (академия), 1 — факультет, 2 — кафедра и т.д.',
            'can_have_children': 'Может ли это подразделение иметь дочерние подразделения',
        }
    
    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if slug:
            import re
            if not re.match(r'^[a-z0-9-]+$', slug):
                raise forms.ValidationError(
                    'Слаг может содержать только строчные латинские буквы, цифры и дефис.'
                )
        return slug