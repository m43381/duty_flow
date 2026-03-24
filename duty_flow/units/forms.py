from django import forms
from .models import Unit, UnitType
from users_app.access_service import AccessService


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


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'unit_type', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Введите название подразделения'
            }),
            'unit_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'parent': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            access = AccessService(self.user)
            visible_units = access.get_visible_units()
            
            # Ограничиваем выбор типов подразделений
            # Для академии - все типы, для остальных - только соответствующие уровни
            if access.user_level == 0:
                # Академия может создавать любые типы
                self.fields['unit_type'].queryset = UnitType.objects.all()
            else:
                # Для факультета и ниже - только типы их уровня или ниже
                allowed_levels = range(access.user_level, access.user_level + 2)
                self.fields['unit_type'].queryset = UnitType.objects.filter(
                    level__in=allowed_levels
                )
            
            # Ограничиваем выбор родителя только видимыми подразделениями
            self.fields['parent'].queryset = visible_units
            self.fields['parent'].empty_label = '— Корневое —'
            
            # Если редактируем существующее подразделение
            if self.instance and self.instance.pk:
                # Нельзя выбрать себя или потомков в качестве родителя
                descendants_ids = self.instance.get_descendants_ids()
                self.fields['parent'].queryset = visible_units.exclude(
                    id__in=descendants_ids + [self.instance.id]
                )
    
    def clean_parent(self):
        parent = self.cleaned_data.get('parent')
        unit_type = self.cleaned_data.get('unit_type')
        
        if parent and unit_type:
            # Проверка: родитель должен иметь возможность иметь детей
            if not parent.unit_type.can_have_children:
                raise forms.ValidationError(
                    f'Подразделение типа "{parent.unit_type.name}" не может иметь дочерние подразделения'
                )
            
            # Проверка: уровень родителя должен быть меньше уровня дочернего
            if parent.get_level() >= unit_type.level:
                raise forms.ValidationError(
                    f'Уровень родителя ({parent.get_level()}) должен быть меньше '
                    f'уровня дочернего подразделения ({unit_type.level})'
                )
        
        return parent