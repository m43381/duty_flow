from django.db import models
from django.core.exceptions import ValidationError
from units.models import Unit
from ranks.models import Rank
from duty_types.models import DutyType

class Person(models.Model):
    """Сотрудник (участник нарядов)"""
    last_name = models.CharField(max_length=150, verbose_name="Фамилия", db_index=True)
    first_name = models.CharField(max_length=150, verbose_name="Имя")
    middle_name = models.CharField(max_length=150, blank=True, verbose_name="Отчество")
    rank = models.ForeignKey(Rank, on_delete=models.PROTECT, related_name='people', verbose_name="Звание")
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='people', verbose_name="Подразделение")

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
        ]

    def __str__(self):
        return f"{self.rank.name} {self.last_name} {self.first_name} {self.middle_name}".strip()

    def full_name(self):
         return f"{self.last_name} {self.first_name} {self.middle_name}".strip()
    full_name.short_description = "Полное имя"


class Exemption(models.Model):
    """Освобождение от нарядов"""
    REASON_CHOICES = [
        ('illness', 'Болезнь'),
        ('leave', 'Отпуск'),
        ('trip', 'Командировка'),
        ('other', 'Другое'),
    ]
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='exemptions', verbose_name="Сотрудник")
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, verbose_name="Причина")
    date_from = models.DateField(verbose_name="Дата начала")
    date_to = models.DateField(verbose_name="Дата окончания")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Освобождение"
        verbose_name_plural = "Освобождения"
        ordering = ['-date_from']

    def __str__(self):
        return f"{self.person} - {self.get_reason_display()} ({self.date_from} - {self.date_to})"

    def clean(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError("Дата начала не может быть позже даты окончания.")


class DutyClearance(models.Model):
    """Допуск сотрудника к типу наряда"""
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='clearances', verbose_name="Сотрудник")
    duty_type = models.ForeignKey(DutyType, on_delete=models.CASCADE, related_name='clearances', verbose_name="Тип наряда")

    class Meta:
        verbose_name = "Допуск к наряду"
        verbose_name_plural = "Допуски к нарядам"
        unique_together = ('person', 'duty_type') # У одного человека не может быть двух одинаковых допусков

    def __str__(self):
        return f"{self.person} допущен к {self.duty_type}"