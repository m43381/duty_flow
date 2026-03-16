from django.db import models

class UnitType(models.Model):
    """Тип подразделения"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Название типа")
    slug = models.SlugField(max_length=50, unique=True, verbose_name="Слаг")
    level = models.PositiveSmallIntegerField(
        default=0, 
        verbose_name="Уровень иерархии",
        help_text="0 - самый высокий уровень (академия), 1 - факультет, 2 - кафедра и т.д."
    )
    can_have_children = models.BooleanField(
        default=True,
        verbose_name="Может иметь дочерние подразделения"
    )
    
    class Meta:
        verbose_name = "Тип подразделения"
        verbose_name_plural = "Типы подразделений"
        ordering = ['level', 'name']

    def __str__(self):
        return f"{self.name} (уровень {self.level})"

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
        on_delete=models.PROTECT,
        related_name='units',
        verbose_name="Тип подразделения"
    )
    
    class Meta:
        verbose_name = "Подразделение"
        verbose_name_plural = "Подразделения"
        ordering = ['unit_type__level', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.unit_type.name})"
    
    def get_level(self):
        """Получить уровень подразделения в иерархии"""
        return self.unit_type.level
    
    def get_all_children(self):
        """Получить все дочерние подразделения (рекурсивно)"""
        children = []
        for child in self.children.all():
            children.append(child)
            children.extend(child.get_all_children())
        return children
    
    def get_descendants_ids(self, include_self=False):
        """Получить ID всех дочерних подразделений"""
        ids = [self.id] if include_self else []
        
        def collect(child):
            for c in child.children.all():
                ids.append(c.id)
                collect(c)
        
        collect(self)
        return ids
    
    def get_ancestors(self):
        """Получить все вышестоящие подразделения"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors