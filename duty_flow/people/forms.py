from django import forms
from .models import Person, Exemption, DutyClearance
from ranks.models import Rank
from units.models import Unit
from duty_types.models import DutyType

# ========== Форма для сотрудников ==========
class PersonForm(forms.ModelForm):
    """Форма для добавления/редактирования сотрудника"""
    
    class Meta:
        model = Person
        fields = ['last_name', 'first_name', 'middle_name', 'rank', 'unit']
        widgets = {
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Введите фамилию'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Введите имя'
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Введите отчество (необязательно)'
            }),
            'rank': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Сортируем звания
        self.fields['rank'].queryset = Rank.objects.all().order_by('order')
        
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


# ========== Форма для освобождений ==========
class ExemptionForm(forms.ModelForm):
    """Форма для освобождения"""
    
    class Meta:
        model = Exemption
        fields = ['reason', 'date_from', 'date_to', 'comment']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'date_from': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
            }),
            'date_to': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Комментарий (необязательно)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_from'].input_formats = ['%Y-%m-%d', '%d.%m.%Y']
        self.fields['date_to'].input_formats = ['%Y-%m-%d', '%d.%m.%Y']
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to:
            if date_from > date_to:
                raise forms.ValidationError('Дата начала не может быть позже даты окончания')
        
        return cleaned_data


# ========== Форма для допусков ==========
class DutyClearanceForm(forms.ModelForm):
    """Форма для допуска"""
    
    class Meta:
        model = DutyClearance
        fields = ['duty_type']
        widgets = {
            'duty_type': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop('person', None)
        super().__init__(*args, **kwargs)
        self.fields['duty_type'].queryset = DutyType.objects.all().order_by('name')
        self.fields['duty_type'].label = 'Тип наряда'
        
        # Исключаем уже существующие допуски
        if self.person:
            existing_ids = DutyClearance.objects.filter(person=self.person).values_list('duty_type_id', flat=True)
            self.fields['duty_type'].queryset = self.fields['duty_type'].queryset.exclude(id__in=existing_ids)