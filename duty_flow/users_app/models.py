from django.db import models
from django.contrib.auth.models import User
from units.models import Unit


class UserProfile(models.Model):
    """Профиль пользователя-оператора"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.PROTECT, 
        related_name='users'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users',
        verbose_name="Создал пользователь"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"{self.user.username} - {self.unit.name} ({self.unit.unit_type.name})"
    
    @property
    def level(self):
        """Уровень пользователя в иерархии"""
        return self.unit.unit_type.level
    
    @property
    def unit_type(self):
        """Тип подразделения пользователя"""
        return self.unit.unit_type.name