from django import forms
from .models import Person
from ranks.models import Rank

class PersonForm(forms.ModelForm):
    """Форма для добавления/редактирования сотрудника"""
    
    class Meta:
        model = Person
        fields = ['last_name', 'first_name', 'middle_name', 'rank']  # убрали unit
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
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Сортируем звания
        self.fields['rank'].queryset = Rank.objects.all().order_by('order')