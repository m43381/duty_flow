from django.db import models
from django.conf import settings
from units.models import Unit
from duty_types.models import DutyType
from people.models import Person


class MonthlySchedule(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликовано'),
        ('archived', 'Архив'),
    ]
    
    month = models.DateField()
    name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='schedules')
    parent_schedule = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-month']
        unique_together = ['month', 'unit']  # ← уникальность: один месяц + одно подразделение
    
    def __str__(self):
        return self.name or f"{self.month.strftime('%B %Y')} - {self.unit.name}"


class DayPlan(models.Model):
    TYPE_CHOICES = [
        ('own', 'Свой наряд'),
        ('incoming', 'Входящий наряд'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Ожидает принятия'),
        ('accepted', 'Принято'),
    ]
    CHILD_STATUS_CHOICES = [
        ('none', 'Нет дочерних'),
        ('pending', 'Ожидает принятия'),
        ('accepted', 'Принято дочерним'),
    ]
    
    schedule = models.ForeignKey(MonthlySchedule, on_delete=models.CASCADE, related_name='days')
    date = models.DateField()
    duty_type = models.ForeignKey(DutyType, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, null=True, blank=True)
    
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='own')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)
    child_status = models.CharField(max_length=20, choices=CHILD_STATUS_CHOICES, default='none')
    
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('schedule', 'date', 'duty_type')
    
    def __str__(self):
        return f"{self.date}: {self.duty_type.name} → {self.unit.name if self.unit else '—'}"



class DutyAssignment(models.Model):
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