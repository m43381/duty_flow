from django.db import models
from units.models import Unit
from duty_plans.models import DutyPlan
from duty_types.models import DutyType


class AccessService:
    """
    Универсальный сервис для проверки прав доступа
    Основан на уровнях иерархии подразделений
    """
    
    def __init__(self, user):
        self.user = user
        self.profile = user.profile
        self.user_unit = user.profile.unit
        self.user_level = self.user_unit.unit_type.level  # статический уровень
    
    # ========== ПОДРАЗДЕЛЕНИЯ ==========
    
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
        return unit.id in self.user_unit.get_descendants_ids(include_self=True)
    
    def can_edit_unit(self, unit):
        """Может ли редактировать подразделение"""
        return unit.id == self.user_unit.id
    
    # ========== ТИПЫ НАРЯДОВ ==========
    
    def get_available_duty_types(self):
        """
        Типы нарядов, которые пользователь может использовать для планирования.
        Правила:
        - Типы, закрепленные за своим подразделением
        - Типы, закрепленные за вышестоящими подразделениями (для кафедр)
        """
        # Свои типы
        own_types = DutyType.objects.filter(unit=self.user_unit)
        
        # Типы вышестоящих (если есть)
        parent_types = DutyType.objects.none()
        if self.user_unit.parent:
            parent_types = DutyType.objects.filter(unit=self.user_unit.parent)
        
        return (own_types | parent_types).distinct()
    
    # ========== ПЛАНЫ НАРЯДОВ ==========
    
    def get_visible_plans(self):
        """
        Планы, которые пользователь может видеть:
        - Планы своего подразделения
        - Планы дочерних подразделений
        - Если план имеет parent_plan, виден и он
        """
        visible_units = self.get_visible_units()
        
        # Планы видимых подразделений
        plans = DutyPlan.objects.filter(unit__in=visible_units)
        
        # Добавляем родительские планы (для отслеживания иерархии)
        parent_ids = plans.filter(parent_plan__isnull=False).values_list('parent_plan_id', flat=True)
        plans = plans | DutyPlan.objects.filter(id__in=parent_ids)
        
        return plans.distinct()
    
    def get_plans_for_planning(self):
        """
        Планы, которые пользователь может "принять" (создать дочерние).
        Только корневые планы для подчиненных подразделений.
        """
        return DutyPlan.objects.filter(
            unit=self.user_unit,
            parent_plan__isnull=True
        )
    
    def can_create_plan(self, target_unit=None):
        """
        Может ли пользователь создавать планы.
        Если target_unit указан — проверяем конкретное подразделение.
        """
        if target_unit is None:
            return True
        
        # Создание для подчиненных (глубина 1)
        return target_unit.parent_id == self.user_unit.id
    
    def can_edit_plan(self, plan):
        """
        Может ли пользователь редактировать план.
        """
        return plan.unit.id == self.user_unit.id or plan.created_by_id == self.user.id
    
    def can_delete_plan(self, plan):
        """
        Может ли пользователь удалять план.
        """
        return plan.created_by_id == self.user.id
    
    # ========== НАЗНАЧЕНИЯ ==========
    
    def can_assign_person(self, plan, person):
        """
        Может ли пользователь назначить сотрудника на план.
        """
        if plan.unit.id != self.user_unit.id:
            return False
        
        if person.unit.id != self.user_unit.id:
            return False
        
        if not person.clearances.filter(duty_type=plan.duty_type).exists():
            return False
        
        if person.exemptions.filter(
            date_from__lte=plan.date,
            date_to__gte=plan.date
        ).exists():
            return False
        
        return True
    
    # ========== УНИВЕРСАЛЬНЫЕ МЕТОДЫ ==========
    
    def get_visible_queryset(self, queryset):
        """Универсальная фильтрация queryset'а"""
        visible_units = self.get_visible_units()
        return queryset.filter(unit__in=visible_units)
    
    def can_view_object(self, obj):
        """Может ли просматривать объект"""
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
        return int(unit_id) == self.user_unit.id
    
    # ========== КОНТЕКСТ ДЛЯ ШАБЛОНОВ ==========
    
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
        
        root_units = []
        all_units = list(visible_units)
        for unit in all_units:
            if unit.parent is None or unit.parent not in all_units:
                if unit.id not in [r['id'] for r in root_units]:
                    root_units.append(build_tree(unit))
        
        return {
            'units_tree': root_units,
            'current_unit_id': self.user_unit.id,
            'current_unit_name': self.user_unit.name,
            'current_level': self.user_level,
        }
    
    def get_planning_context(self):
        """Контекст для страницы планирования"""
        return {
            'available_units': self.get_visible_units(),
            'available_duty_types': self.get_available_duty_types(),
            'can_create_plan': self.can_create_plan(),
            'plans_for_planning': self.get_plans_for_planning(),
        }