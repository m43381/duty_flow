from django.db import models
from django.conf import settings
from units.models import Unit
from people.models import DutyType, Person

class DutyPlan(models.Model):
    """
    План наряда на конкретную дату для конкретного подразделения.
    
    Иерархия:
    - Если parent_plan = None — корневой план (создан вышестоящим подразделением)
    - Если parent_plan указан — дочерний план (создан нижестоящим подразделением 
      на основе корневого)
    """
    # Основные поля
    date = models.DateField(db_index=True, verbose_name="Дата наряда")
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='duty_plans', 
        verbose_name="Подразделение"
    )
    duty_type = models.ForeignKey(
        DutyType, 
        on_delete=models.CASCADE, 
        related_name='duty_plans', 
        verbose_name="Тип наряда"
    )
    
    # Иерархия
    parent_plan = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_plans',
        verbose_name="Создан на основе плана"
    )
    
    # Аудит
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_plans',
        verbose_name="Создал"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Дата обновления"
    )
    
    class Meta:
        verbose_name = "План наряда"
        verbose_name_plural = "Планы нарядов"
        ordering = ['-date', 'unit']
        # На одно подразделение в один день не может быть двух одинаковых нарядов
        unique_together = ('date', 'unit', 'duty_type')
        indexes = [
            models.Index(fields=['date', 'unit']),
            models.Index(fields=['parent_plan']),
        ]

    def __str__(self):
        return f"{self.date}: {self.unit} - {self.duty_type}"
    
    @property
    def is_root(self):
        """Корневой ли план (создан вышестоящим)"""
        return self.parent_plan is None
    
    @property
    def is_child(self):
        """Дочерний ли план (создан нижестоящим)"""
        return self.parent_plan is not None
    
    def get_origin_plan(self):
        """Получить корневой план (первоисточник)"""
        if self.is_root:
            return self
        return self.parent_plan.get_origin_plan()
    
    def get_creation_chain(self):
        """Получить цепочку создания (от корня до текущего)"""
        chain = []
        current = self
        while current:
            chain.append(current)
            current = current.parent_plan
        return list(reversed(chain))


class DutyAssignment(models.Model):
    """
    Назначение конкретного сотрудника на план наряда.
    """
    plan = models.ForeignKey(
        DutyPlan, 
        on_delete=models.CASCADE, 
        related_name='assignments', 
        verbose_name="План"
    )
    person = models.ForeignKey(
        Person, 
        on_delete=models.CASCADE, 
        related_name='duty_assignments', 
        verbose_name="Сотрудник"
    )
    
    # Аудит
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_duties',
        verbose_name="Назначил"
    )
    assigned_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Дата назначения"
    )
    
    class Meta:
        verbose_name = "Назначение на наряд"
        verbose_name_plural = "Назначения на наряды"
        # Один сотрудник не может быть дважды назначен на один и тот же план
        unique_together = ('plan', 'person')
        indexes = [
            models.Index(fields=['plan', 'person']),
        ]

    def __str__(self):
        return f"{self.person} назначен в {self.plan}"