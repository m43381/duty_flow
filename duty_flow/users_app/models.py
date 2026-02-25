from django.db import models
from django.contrib.auth.models import User
from units.models import Unit

class UserProfile(models.Model):
    """Профиль пользователя-оператора"""
    ACCESS_LEVEL_CHOICES = [
        ('academy', 'Академия'),
        ('faculty', 'Факультет'),
        ('department', 'Кафедра'),
        ('commandant', 'Комендант'),
    ]
    
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
    access_level = models.CharField(
        max_length=20, 
        choices=ACCESS_LEVEL_CHOICES
    )

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"{self.user.username} - {self.unit} ({self.get_access_level_display()})"