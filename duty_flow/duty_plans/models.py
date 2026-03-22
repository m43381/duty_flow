from django.db import models
from django.conf import settings
from units.models import Unit
from duty_types.models import DutyType
from people.models import Person


class MonthlySchedule(models.Model):
    """
    Расписание на месяц (не привязано к конкретному подразделению)
    """
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликовано'),
        ('archived', 'Архив'),
    ]
    
    month = models.DateField(verbose_name="Месяц", help_text="Всегда первое число месяца")
    name = models.CharField(max_length=255, blank=True, verbose_name="Название")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Статус")
    
    # Иерархия
    parent_schedule = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_schedules',
        verbose_name="Создано на основе расписания"
    )
    
    # Аудит
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_schedules',
        verbose_name="Создал"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Расписание на месяц"
        verbose_name_plural = "Расписания на месяц"
        ordering = ['-month']
        unique_together = ('month', 'created_by')
    
    def __str__(self):
        return self.name or self.month.strftime('%B %Y')
    
    def save(self, *args, **kwargs):
        if self.month:
            self.month = self.month.replace(day=1)
        super().save(*args, **kwargs)
    
    def publish(self):
        """Опубликовать расписание"""
        self.status = 'published'
        self.save()
        # TODO: создать входящие назначения для дочерних подразделений


class DayPlan(models.Model):
    """
    Назначение на конкретный день
    """
    EXECUTION_CHOICES = [
        ('own', 'Силами своего аппарата'),
        ('delegate', 'Делегировать подразделению'),
    ]
    
    schedule = models.ForeignKey(
        MonthlySchedule,
        on_delete=models.CASCADE,
        related_name='days',
        verbose_name="Расписание"
    )
    date = models.DateField(verbose_name="Дата")
    duty_type = models.ForeignKey(
        DutyType,
        on_delete=models.CASCADE,
        related_name='day_plans',
        verbose_name="Тип наряда"
    )
    
    # Исполнитель
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='assigned_day_plans',
        verbose_name="Подразделение-исполнитель"
    )
    execution_type = models.CharField(
        max_length=20,
        choices=EXECUTION_CHOICES,
        default='own',
        verbose_name="Способ исполнения"
    )
    
    # Связь с родительским назначением (откуда пришло)
    parent_day_plan = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_plans',
        verbose_name="Создано на основе назначения"
    )
    
    # Аудит
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "План на день"
        verbose_name_plural = "Планы на день"
        ordering = ['date']
        unique_together = ('schedule', 'date', 'duty_type')
    
    def __str__(self):
        unit_name = self.unit.name if self.unit else "не назначено"
        return f"{self.date}: {self.duty_type.name} → {unit_name}"
    
    @property
    def is_own_execution(self):
        return self.execution_type == 'own'
    
    @property
    def is_delegated(self):
        return self.execution_type == 'delegate' and self.unit


class DutyAssignment(models.Model):
    """
    Назначение конкретного сотрудника на план дня (пока не используется)
    """
    day_plan = models.ForeignKey(
        DayPlan,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name="План на день"
    )
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='duty_assignments',
        verbose_name="Сотрудник"
    )
    
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_duties',
        verbose_name="Назначил"
    )
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата назначения")
    
    class Meta:
        verbose_name = "Назначение на наряд"
        verbose_name_plural = "Назначения на наряды"
        unique_together = ('day_plan', 'person')
    
    def __str__(self):
        return f"{self.person} → {self.day_plan}"