from django.db import models
from units.models import Unit


class DutyType(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    required_people = models.PositiveSmallIntegerField(default=1, verbose_name="Требуется человек")
    
    created_by_unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name='created_duty_types',
        verbose_name="Создано подразделением"
    )
    
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_duty_types',
        verbose_name="Закрепленное подразделение (опционально)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Тип наряда"
        verbose_name_plural = "Типы нарядов"
        ordering = ['name']
    
    def __str__(self):
        if self.unit:
            return f"{self.name} → {self.unit.name}"
        return self.name