from units.models import Unit

class AccessService:
    """
    Универсальный сервис для проверки прав доступа
    Основан на уровнях иерархии подразделений
    """
    
    def __init__(self, user):
        self.user = user
        self.profile = user.profile
        self.user_unit = user.profile.unit
        self.user_level = user.profile.unit.unit_type.level
    
    def get_visible_units(self):
        """
        Все подразделения, которые пользователь может видеть:
        - Своё подразделение
        - Все дочерние (любой глубины)
        """
        descendant_ids = self.user_unit.get_descendants_ids(include_self=True)
        return Unit.objects.filter(id__in=descendant_ids)
    
    def get_editable_units(self):
        """
        Подразделения, которые пользователь может редактировать:
        - Только своё подразделение
        """
        return Unit.objects.filter(id=self.user_unit.id)
    
    def can_view_unit(self, unit):
        """Может ли просматривать подразделение"""
        # Своё или дочернее
        return unit.id in self.user_unit.get_descendants_ids(include_self=True)
    
    def can_edit_unit(self, unit):
        """Может ли редактировать подразделение"""
        # Только своё
        return unit.id == self.user_unit.id
    
    def get_visible_queryset(self, queryset):
        """
        Универсальный метод для фильтрации любого queryset'а
        Модель должна иметь поле 'unit' (ForeignKey на Unit)
        """
        visible_units = self.get_visible_units()
        return queryset.filter(unit__in=visible_units)
    
    def get_editable_queryset(self, queryset):
        """
        Queryset объектов, которые можно редактировать
        """
        editable_units = self.get_editable_units()
        return queryset.filter(unit__in=editable_units)
    
    def can_view_object(self, obj):
        """Может ли просматривать объект (любая модель с unit)"""
        if not hasattr(obj, 'unit'):
            return True
        return self.can_view_unit(obj.unit)
    
    def can_edit_object(self, obj):
        """Может ли редактировать объект"""
        if not hasattr(obj, 'unit'):
            return False
        return self.can_edit_unit(obj.unit)
    
    def can_create_in_unit(self, unit_id):
        """Может ли создавать объекты в указанном подразделении"""
        # Создавать можно только в своём подразделении
        return int(unit_id) == self.user_unit.id
    
    def get_filter_context(self):
        """Контекст для фильтров в шаблонах"""
        visible_units = self.get_visible_units()
        
        def build_tree(unit):
            children = unit.children.filter(id__in=visible_units)
            return {
                'id': unit.id,
                'name': unit.name,
                'type': unit.unit_type.name,
                'level': unit.unit_type.level,
                'children': [build_tree(child) for child in children]
            }
        
        # Начинаем с корневых
        root_units = []
        all_units = list(visible_units)
        for unit in all_units:
            if unit.parent is None or unit.parent not in all_units:
                if unit not in [r['id'] for r in root_units]:
                    root_units.append(build_tree(unit))
        
        return {
            'units_tree': root_units,
            'current_unit_id': self.user_unit.id,
            'current_unit_name': self.user_unit.name,
            'current_level': self.user_level,
        }