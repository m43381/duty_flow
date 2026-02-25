from django.db import models

class Rank(models.Model):
    """Звание"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Звание")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок") # Для сортировки (рядовой -> генерал)

    class Meta:
        verbose_name = "Звание"
        verbose_name_plural = "Звания"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name