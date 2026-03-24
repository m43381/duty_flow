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
            
            # Получаем подразделения, в которых можно создавать
            available_parents = access.get_available_parents_for_creation()
            
            # Формируем выбор родителя с отображением иерархии
            parent_choices = []
            
            for parent in available_parents:
                # Формируем отображаемое имя с учетом иерархии
                display_name = self._get_parent_display_name(parent)
                parent_choices.append((parent.id, display_name))
            
            # Добавляем пустой вариант для корневых подразделений
            self.fields['parent'].choices = [('', '— Корневое (без родителя) —')] + parent_choices
            
            # Если редактируем существующее подразделение
            if self.instance and self.instance.pk:
                # Нельзя выбрать себя или потомков в качестве родителя
                descendants_ids = self.instance.get_descendants_ids()
                forbidden_ids = descendants_ids + [self.instance.id]
                
                # Фильтруем доступных родителей
                self.fields['parent'].queryset = available_parents.exclude(
                    id__in=forbidden_ids
                )
                
                # Перестраиваем choices
                self._update_parent_choices()
            
            # Фильтрация типов подразделений
            self._filter_unit_types()
    
    def _get_parent_display_name(self, unit, level=0, max_level=3):
        """
        Формирует отображаемое имя родителя с учетом иерархии
        """
        indent = '　' * level  # Используем японский пробел для отступа
        ancestors = unit.get_ancestors()
        
        if ancestors:
            path = ' → '.join([a.name for a in reversed(ancestors)])
            return f"{indent}{unit.name} ({unit.unit_type.name}) [ {path} ]"
        else:
            return f"{indent}{unit.name} ({unit.unit_type.name})"
    
    def _update_parent_choices(self):
        """Обновляет choices для поля parent"""
        parent_choices = []
        
        for parent in self.fields['parent'].queryset:
            display_name = self._get_parent_display_name(parent)
            parent_choices.append((parent.id, display_name))
        
        self.fields['parent'].choices = [('', '— Корневое (без родителя) —')] + parent_choices
    
    def _filter_unit_types(self):
        """
        Фильтрация доступных типов подразделений:
        - Можно создавать только типы с уровнем ВЫШЕ, чем у родителя
        """
        parent = self.cleaned_data.get('parent') if self.is_bound else self.initial.get('parent')
        
        if parent and isinstance(parent, Unit):
            # Если родитель выбран, показываем только типы с уровнем > уровня родителя
            allowed_levels = range(parent.get_level() + 1, 100)
            self.fields['unit_type'].queryset = UnitType.objects.filter(
                level__in=allowed_levels
            )
        else:
            # Если родитель не выбран (корневое), показываем типы с уровнем 0
            self.fields['unit_type'].queryset = UnitType.objects.filter(level=0)
        
        # Если пользователь не академия, ограничиваем также уровнем пользователя
        if self.user:
            access = AccessService(self.user)
            if access.user_level != 0:
                # Не-академия может создавать только типы с уровнем выше своего
                allowed_levels = range(access.user_level + 1, 100)
                self.fields['unit_type'].queryset = self.fields['unit_type'].queryset.filter(
                    level__in=allowed_levels
                )
    
    def clean_parent(self):
        """Валидация родителя"""
        parent = self.cleaned_data.get('parent')
        unit_type = self.cleaned_data.get('unit_type')
        
        if parent and unit_type:
            # Проверка: родитель должен иметь возможность иметь детей
            if not parent.unit_type.can_have_children:
                raise forms.ValidationError(
                    f'Подразделение "{parent.name}" (тип: {parent.unit_type.name}) '
                    f'не может иметь дочерние подразделения'
                )
            
            # Проверка: уровень родителя должен быть меньше уровня дочернего
            if parent.get_level() >= unit_type.level:
                raise forms.ValidationError(
                    f'Нельзя создать подразделение типа "{unit_type.name}" (уровень {unit_type.level}) '
                    f'в подразделении "{parent.name}" (уровень {parent.get_level()}). '
                    f'Уровень дочернего подразделения должен быть выше уровня родителя.'
                )
        
        return parent
    
    def clean(self):
        """Общая валидация формы"""
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        unit_type = cleaned_data.get('unit_type')
        
        if not parent and unit_type:
            # Корневое подразделение - проверяем, что тип имеет уровень 0
            if unit_type.level != 0:
                raise forms.ValidationError(
                    f'Корневое подразделение может быть только типа с уровнем 0. '
                    f'Выбран тип "{unit_type.name}" (уровень {unit_type.level})'
                )
        
        return cleaned_data