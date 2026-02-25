from django.db import models
from units.models import Unit
from people.models import DutyType, Person

class DutyPlan(models.Model):
    """План наряда на конкретную дату"""
    date = models.DateField(db_index=True, verbose_name="Дата наряда")
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='duty_plans', verbose_name="Подразделение")
    duty_type = models.ForeignKey(DutyType, on_delete=models.CASCADE, related_name='duty_plans', verbose_name="Тип наряда")

    class Meta:
        verbose_name = "План наряда"
        verbose_name_plural = "Планы нарядов"
        ordering = ['-date', 'unit']
        # На одно подразделение в один день не может быть двух одинаковых нарядов
        unique_together = ('date', 'unit', 'duty_type')

    def __str__(self):
        return f"{self.date}: {self.unit} - {self.duty_type}"


class DutyAssignment(models.Model):
    """Назначение конкретного сотрудника на план наряда"""
    plan = models.ForeignKey(DutyPlan, on_delete=models.CASCADE, related_name='assignments', verbose_name="План")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='duty_assignments', verbose_name="Сотрудник")

    class Meta:
        verbose_name = "Назначение на наряд"
        verbose_name_plural = "Назначения на наряды"
        # Один сотрудник не может быть дважды назначен на один и тот же план
        unique_together = ('plan', 'person')

    def __str__(self):
        return f"{self.person} назначен в {self.plan}"