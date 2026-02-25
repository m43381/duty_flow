from django.db import models

class DutyType(models.Model):
    """Тип наряда"""
    name = models.CharField(max_length=150, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    required_people = models.PositiveSmallIntegerField(default=1, verbose_name="Требуется человек")

    class Meta:
        verbose_name = "Тип наряда"
        verbose_name_plural = "Типы нарядов"
        ordering = ['name']

    def __str__(self):
        return self.name
