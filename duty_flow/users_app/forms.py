from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from units.models import Unit
from users_app.access_service import AccessService


class UserCreateForm(forms.ModelForm):
    """Форма создания пользователя"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input'}),
        validators=[validate_password],
        label="Пароль",
        help_text="Минимум 8 символов, не должен быть слишком простым"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input'}),
        label="Подтверждение пароля"
    )
    unit = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Подразделение"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.request_user:
            access = AccessService(self.request_user)
            
            # Собираем доступные подразделения: свое и прямые дочерние
            available_units = []
            
            # Свое подразделение (можно создать помощника)
            available_units.append(access.user_unit)
            
            # Прямые дочерние подразделения (можно создать руководителя)
            for child in access.user_unit.children.all():
                available_units.append(child)
            
            # Формируем choices с понятными названиями
            choices = []
            for unit in available_units:
                if unit.id == access.user_unit.id:
                    label = f"{unit.name} ({unit.unit_type.name}) - ваше подразделение (создать помощника)"
                else:
                    label = f"{unit.name} ({unit.unit_type.name}) - дочернее подразделение (создать руководителя)"
                choices.append((unit.id, label))
            
            self.fields['unit'].choices = choices
            
            # Устанавливаем значение по умолчанию - свое подразделение
            if choices:
                self.initial['unit'] = access.user_unit.id
            
            self.fields['unit'].help_text = "Выберите подразделение для нового пользователя"
    
    def clean_unit(self):
        """Проверка, что выбранное подразделение допустимо"""
        unit_id = self.cleaned_data.get('unit')
        if not unit_id:
            raise forms.ValidationError('Выберите подразделение')
        
        try:
            unit = Unit.objects.get(pk=unit_id)
        except Unit.DoesNotExist:
            raise forms.ValidationError('Выбранное подразделение не существует')
        
        # Проверяем, что пользователь может создавать в этом подразделении
        if self.request_user:
            access = AccessService(self.request_user)
            if not access.can_create_user_for_unit(unit):
                raise forms.ValidationError(
                    'Вы не можете создать пользователя в этом подразделении. '
                    'Доступны только ваше подразделение и прямые дочерние.'
                )
        
        return unit_id
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с таким логином уже существует')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Пароли не совпадают')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        
        if commit:
            user.save()
            from users_app.models import UserProfile
            UserProfile.objects.create(
                user=user,
                unit_id=self.cleaned_data['unit'],
                created_by=self.request_user
            )
        
        return user


class UserEditForm(forms.ModelForm):
    """Форма редактирования пользователя"""
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'readonly': 'readonly'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.request_user:
            access = AccessService(self.request_user)
            
            # Убираем поле подразделения - нельзя менять
            self.fields.pop('unit', None)
            
            # Если пользователь не академия, нельзя менять is_active
            if access.user_level != 0:
                self.fields['is_active'].widget.attrs['disabled'] = 'disabled'
                self.fields['is_active'].help_text = "Только администратор может активировать/деактивировать пользователей"
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        if commit:
            user.save()
        
        return user


class UserChangePasswordForm(forms.Form):
    """Форма смены пароля"""
    
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input'}),
        validators=[validate_password],
        label="Новый пароль",
        help_text="Минимум 8 символов, не должен быть слишком простым"
    )
    new_password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input'}),
        label="Подтверждение нового пароля"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('new_password')
        confirm = cleaned_data.get('new_password_confirm')
        
        if password and confirm and password != confirm:
            raise forms.ValidationError('Пароли не совпадают')
        
        return cleaned_data