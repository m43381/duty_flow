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
    unit = forms.ModelChoiceField(
        queryset=Unit.objects.none(),
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
            # Показываем подразделения, в которых можно создавать пользователей
            # Это: свое и прямые дочерние
            available_units = [access.user_unit]
            available_units.extend(access.user_unit.children.all())
            self.fields['unit'].queryset = Unit.objects.filter(id__in=[u.id for u in available_units])
            self.fields['unit'].help_text = "Вы можете создать пользователя в своем подразделении или в прямом дочернем"
    
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
                unit=self.cleaned_data['unit']
            )
        
        return user


class UserEditForm(forms.ModelForm):
    """Форма редактирования пользователя"""
    
    unit = forms.ModelChoiceField(
        queryset=Unit.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Подразделение",
        required=True
    )
    
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
            
            # Для редактирования показываем все подразделения, которые может видеть пользователь
            visible_units = access.get_visible_units()
            self.fields['unit'].queryset = visible_units
            
            # Устанавливаем текущее подразделение
            if self.instance and hasattr(self.instance, 'profile'):
                self.initial['unit'] = self.instance.profile.unit_id
            
            # Если пользователь не академия, нельзя менять is_active
            if access.user_level != 0:
                self.fields['is_active'].widget.attrs['disabled'] = 'disabled'
                self.fields['is_active'].help_text = "Только администратор может активировать/деактивировать пользователей"
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        if commit:
            user.save()
            if hasattr(user, 'profile'):
                user.profile.unit = self.cleaned_data['unit']
                user.profile.save()
        
        return user


class UserChangePasswordForm(forms.Form):
    """Форма смены пароля"""
    
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input'}),
        validators=[validate_password],
        label="Новый пароль"
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