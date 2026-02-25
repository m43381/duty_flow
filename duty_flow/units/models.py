from django.db import models

class UnitType(models.Model):
    """Тип подразделения (вынесено в отдельную таблицу)"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Название типа")
    slug = models.SlugField(max_length=50, unique=True, verbose_name="Слаг") # Например: 'academy', 'faculty'

    class Meta:
        verbose_name = "Тип подразделения"
        verbose_name_plural = "Типы подразделений"
        ordering = ['name']

    def __str__(self):
        return self.name

class Unit(models.Model):
    """Подразделение"""
    name = models.CharField(max_length=255, verbose_name="Название")
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Вышестоящее подразделение"
    )
    unit_type = models.ForeignKey(
        UnitType,
        on_delete=models.PROTECT, # Запрещаем удаление типа, если он используется
        related_name='units',
        verbose_name="Тип подразделения"
    )

    class Meta:
        verbose_name = "Подразделение"
        verbose_name_plural = "Подразделения"
        ordering = ['unit_type', 'name']

    def __str__(self):
        return f"{self.get_unit_type_display()}: {self.name}"

    # Для админки можно добавить отображение типа
    def get_unit_type_display(self):
        return self.unit_type.name
    get_unit_type_display.short_description = "Тип"