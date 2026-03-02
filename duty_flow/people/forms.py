from django import forms
from .models import Person
from ranks.models import Rank
from units.models import Unit

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
            'rank': forms.Select(attrs={
                'class': 'form-select'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Сортируем звания по порядку
        self.fields['rank'].queryset = Rank.objects.all().order_by('order')
        
        # Если есть пользователь и это не академия, ограничиваем выбор подразделений
        if self.user and self.user.profile.access_level != 'academy':
            self.fields['unit'].queryset = Unit.objects.filter(id=self.user.profile.unit.id)
            self.fields['unit'].empty_label = None  # Убираем пустой вариант
    
    def clean(self):
        cleaned_data = super().clean()
        unit = cleaned_data.get('unit')
        
        # Проверяем права на создание в этом подразделении
        if self.user and self.user.profile.access_level != 'academy':
            if unit and unit.id != self.user.profile.unit.id:
                raise forms.ValidationError(
                    'Вы можете создавать сотрудников только в своем подразделении'
                )
        
        return cleaned_data