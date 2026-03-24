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
        
        if not self.user:
            return
            
        self.access = AccessService(self.user)
        
        # Настраиваем поле родителя
        self._setup_parent_field()
        
        # Настраиваем поле типа подразделения
        self._setup_unit_type_field()
    
    def _setup_parent_field(self):
        """
        Настройка поля выбора родителя.
        """
        # Получаем все подразделения, в которых можно создавать
        available_parents = self.access.get_available_parents_for_creation()
        
        # Формируем список выбора
        parent_choices = []
        
        # Только академия может создавать корневые подразделения (без родителя)
        if self.access.user_level == 0:
            parent_choices.append(('', '— Корневое (без родителя) —'))
        
        # Добавляем все доступные родители
        for parent in available_parents:
            display_name = f"{parent.name} ({parent.unit_type.name})"
            if parent.parent:
                ancestors = parent.get_ancestors()
                if ancestors:
                    path = ' → '.join([a.name for a in reversed(ancestors)])
                    display_name = f"{display_name} [ {path} ]"
            parent_choices.append((parent.id, display_name))
        
        self.fields['parent'].choices = parent_choices
        
        # Если редактируем существующее подразделение
        if self.instance and self.instance.pk:
            descendants_ids = self.instance.get_descendants_ids()
            forbidden_ids = descendants_ids + [self.instance.id]
            
            filtered_choices = []
            if self.access.user_level == 0:
                filtered_choices.append(('', '— Корневое (без родителя) —'))
            
            for choice in parent_choices:
                if choice[0] and int(choice[0]) not in forbidden_ids:
                    filtered_choices.append(choice)
            
            self.fields['parent'].choices = filtered_choices
    
    def _setup_unit_type_field(self):
        """
        Настройка поля выбора типа подразделения.
        Показываем все типы с уровнем выше уровня пользователя
        """
        min_level = self.access.user_level + 1
        types_qs = UnitType.objects.filter(level__gte=min_level).order_by('level', 'name')
        
        self.fields['unit_type'].queryset = types_qs
        
        help_text = f"Доступны типы с уровнем выше вашего ({self.access.user_level}): "
        help_text += ", ".join([f"{t.name} (ур. {t.level})" for t in types_qs])
        self.fields['unit_type'].help_text = help_text
        
        if not types_qs.exists():
            self.fields['unit_type'].empty_label = '— Нет доступных типов —'
            self.fields['unit_type'].widget.attrs['disabled'] = 'disabled'
    
    def clean_parent(self):
        """
        Валидация родителя
        """
        parent = self.cleaned_data.get('parent')
        
        if parent:
            # Проверка: родитель должен иметь возможность иметь детей
            if not parent.unit_type.can_have_children:
                raise forms.ValidationError(
                    f'Подразделение "{parent.name}" (тип: {parent.unit_type.name}) '
                    f'не может иметь дочерние подразделения'
                )
            
            # Проверка: родитель должен быть видимым для пользователя
            if not self.access.can_view_unit(parent):
                raise forms.ValidationError(
                    f'У вас нет доступа к подразделению "{parent.name}"'
                )
        
        return parent
    
    def clean_unit_type(self):
        """
        Валидация типа подразделения
        """
        unit_type = self.cleaned_data.get('unit_type')
        
        if not unit_type:
            raise forms.ValidationError('Выберите тип подразделения')
        
        # Проверка: тип должен быть выше уровня пользователя
        if unit_type.level <= self.access.user_level:
            raise forms.ValidationError(
                f'Нельзя создать подразделение типа "{unit_type.name}" (уровень {unit_type.level}). '
                f'Ваш уровень {self.access.user_level}. Можно создавать только подразделения '
                f'с уровнем выше вашего.'
            )
        
        return unit_type
    
    def clean(self):
        """
        Общая валидация формы - проверка соответствия родителя и типа
        """
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        unit_type = cleaned_data.get('unit_type')
        
        if not unit_type:
            return cleaned_data
        
        # ========== ОСНОВНЫЕ ПРОВЕРКИ ==========
        
        # Проверка 1: Нельзя создать подразделение своего уровня
        if unit_type.level <= self.access.user_level:
            raise forms.ValidationError(
                f'Нельзя создать подразделение уровня {unit_type.level}, '
                f'так как ваш уровень {self.access.user_level}. '
                f'Можно создавать только подразделения более низкого уровня.'
            )
        
        # Проверка 2: Проверка относительно родителя
        if parent:
            # 2.1: Уровень дочернего должен быть строго выше уровня родителя
            if unit_type.level <= parent.get_level():
                raise forms.ValidationError(
                    f'Нельзя создать подразделение типа "{unit_type.name}" (уровень {unit_type.level}) '
                    f'в подразделении "{parent.name}" (уровень {parent.get_level()}). '
                    f'Уровень дочернего подразделения должен быть ВЫШЕ уровня родителя.'
                )
            
            # 2.2: Проверка иерархической корректности
            # Например: Факультет (level=1) не может быть дочерним для Кафедры (level=2)
            # То есть уровень родителя должен быть МЕНЬШЕ уровня дочернего
            if parent.get_level() >= unit_type.level:
                raise forms.ValidationError(
                    f'Некорректная иерархия: нельзя создать подразделение типа "{unit_type.name}" '
                    f'(уровень {unit_type.level}) в подразделении "{parent.name}" '
                    f'(уровень {parent.get_level()}). Уровень родителя должен быть меньше.'
                )
            
            # 2.3: Проверка типов (дополнительная логическая проверка)
            # Например: Факультет (тип level=1) не может быть дочерним для другого Факультета
            if parent.unit_type.level >= unit_type.level:
                raise forms.ValidationError(
                    f'Некорректная иерархия: тип "{parent.unit_type.name}" (уровень {parent.unit_type.level}) '
                    f'не может быть родителем для типа "{unit_type.name}" (уровень {unit_type.level}). '
                    f'Родительский тип должен иметь более низкий уровень.'
                )
        
        else:
            # Проверка 3: Корневое подразделение (без родителя)
            # Корневое подразделение НЕ МОЖЕТ быть уровня 0
            if unit_type.level == 0:
                raise forms.ValidationError(
                    f'Нельзя создать корневое подразделение типа "{unit_type.name}" (уровень 0). '
                    f'Корневые подразделения могут создаваться только с уровнем 1 и выше.'
                )
            
            # Проверка 4: Только академия может создавать корневые подразделения
            if self.access.user_level != 0:
                raise forms.ValidationError(
                    f'Только администратор (академия) может создавать корневые подразделения.'
                )
        
        # Проверка 5: Дополнительная проверка на циклические ссылки (только для редактирования)
        if self.instance and self.instance.pk and parent:
            if parent.id == self.instance.id:
                raise forms.ValidationError('Подразделение не может быть родителем самого себя.')
            
            # Проверка, что родитель не является потомком текущего подразделения
            descendants_ids = self.instance.get_descendants_ids()
            if parent.id in descendants_ids:
                raise forms.ValidationError(
                    f'Нельзя сделать "{parent.name}" родителем, так как оно является потомком '
                    f'текущего подразделения. Это создаст циклическую ссылку.'
                )
        
        return cleaned_data