from django import forms
from .models import DutyType
from units.models import Unit

class DutyTypeForm(forms.ModelForm):
    """Форма для добавления/редактирования типа наряда"""
    
    class Meta:
        model = DutyType
        fields = ['name', 'description', 'required_people', 'unit']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Введите название типа наряда'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Введите описание',
                'rows': 3
            }),
            'required_people': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'value': 1
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Если пользователь не админ (уровень не 0)
        if self.user and self.user.profile.unit.unit_type.level != 0:
            if 'unit' in self.fields:
                # Для создания: убираем поле unit
                if not self.instance.pk:
                    self.fields.pop('unit')
                else:
                    # Для редактирования: показываем только свое подразделение
                    self.fields['unit'].queryset = Unit.objects.filter(id=self.user.profile.unit.id)
                    self.fields['unit'].empty_label = None
        else:
            # Для админа: показываем все подразделения
            self.fields['unit'].queryset = Unit.objects.all()
            self.fields['unit'].empty_label = "Выберите подразделение"