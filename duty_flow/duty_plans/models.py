from django.db import models
from django.conf import settings
from units.models import Unit
from duty_types.models import DutyType
from people.models import Person


class MonthlySchedule(models.Model):
    """
    Расписание на месяц (черновик или опубликованное)
    """
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликовано'),
        ('archived', 'Архив'),
    ]
    
    month = models.DateField(verbose_name="Месяц", help_text="Всегда первое число месяца")
    name = models.CharField(max_length=255, blank=True, verbose_name="Название")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Статус"
    )
    
    # Подразделение, для которого создано расписание
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name="Подразделение"
    )
    
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
    
    def __str__(self):
        return self.name or f"{self.month.strftime('%B %Y')} - {self.unit.name}"
    
    def save(self, *args, **kwargs):
        if self.month:
            self.month = self.month.replace(day=1)
        super().save(*args, **kwargs)
    
    @property
    def is_root(self):
        return self.parent_schedule is None
    
    def publish(self):
        self.status = 'published'
        self.save()
    
    def archive(self):
        self.status = 'archived'
        self.save()


class DayPlan(models.Model):
    """
    План на конкретный день.
    Принадлежит расписанию на месяц.
    """
    schedule = models.ForeignKey(
        MonthlySchedule,
        on_delete=models.CASCADE,
        related_name='days',
        verbose_name="Расписание на месяц"
    )
    date = models.DateField(verbose_name="Дата")
    
    # Основные поля
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name='day_plans',
        verbose_name="Подразделение"
    )
    duty_type = models.ForeignKey(
        DutyType,
        on_delete=models.CASCADE,
        related_name='day_plans',
        verbose_name="Тип наряда"
    )
    
    # Аудит
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_day_plans',
        verbose_name="Создал"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "План на день"
        verbose_name_plural = "Планы на день"
        ordering = ['date']
        unique_together = ('schedule', 'date', 'duty_type')
    
    def __str__(self):
        return f"{self.date}: {self.unit} - {self.duty_type}"


class DutyAssignment(models.Model):
    """
    Назначение конкретного сотрудника на план дня.
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
    
    # Аудит
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
        return f"{self.person} назначен в {self.day_plan}"