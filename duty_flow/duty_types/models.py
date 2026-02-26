from django.db import models
from units.models import Unit

class DutyType(models.Model):
    """Тип наряда"""
    name = models.CharField(max_length=150, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    required_people = models.PositiveSmallIntegerField(default=1, verbose_name="Требуется человек")
    
    # Поле указывающее на подразделение, создавшее этот тип наряда
    created_by_unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_duty_types',
        verbose_name="Создано подразделением"
    )

    class Meta:
        verbose_name = "Тип наряда"
        verbose_name_plural = "Типы нарядов"
        ordering = ['name']

    def __str__(self):
        return self.name
