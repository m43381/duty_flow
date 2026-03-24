from django.db import models
from units.models import Unit
from duty_plans.models import MonthlySchedule, DayPlan
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
        self.user_level = self.user_unit.unit_type.level
    
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
        - Для академии (level=0): все подразделения
        - Для остальных: своё подразделение + дочерние (на уровень ниже)
        """
        if self.user_level == 0:
            # Академия может редактировать всё
            return Unit.objects.all()
        else:
            # Остальные: своё + дочерние
            editable_ids = [self.user_unit.id]
            for child in self.user_unit.children.all():
                editable_ids.append(child.id)
            return Unit.objects.filter(id__in=editable_ids)
    
    def can_view_unit(self, unit):
        """Может ли просматривать подразделение"""
        if self.user_level == 0:
            # Академия видит всё
            return True
        # Остальные видят только свои и дочерние
        return unit.id in self.user_unit.get_descendants_ids(include_self=True)
    
    def can_edit_unit(self, unit):
        """
        Может ли редактировать подразделение:
        - Академия (level=0): любые подразделения
        - Остальные: своё подразделение + дочерние (прямые потомки)
        """
        if self.user_level == 0:
            return True
        
        # Своё подразделение
        if unit.id == self.user_unit.id:
            return True
        
        # Прямые дочерние подразделения
        if unit.parent and unit.parent.id == self.user_unit.id:
            return True
        
        return False
    
    def can_delete_unit(self, unit):
        """
        Может ли удалять подразделение:
        - Академия (level=0): любые подразделения
        - Остальные: только свои дочерние подразделения (на уровень ниже)
        """
        if self.user_level == 0:
            # Академия может удалять любые подразделения
            return True
        
        # Нельзя удалять своё подразделение
        if unit.id == self.user_unit.id:
            return False
        
        # Можно удалять только прямые дочерние подразделения
        if unit.parent and unit.parent.id == self.user_unit.id:
            return True
        
        return False
    
    def can_create_in_unit(self, unit):
        """
        Может ли пользователь создавать дочерние подразделения в указанном подразделении.
        
        Логика:
        - Пользователь может создавать в любом подразделении, которое:
          1. Находится в иерархии его подразделения (себя или потомки)
          2. Может иметь детей (can_have_children=True)
        """
        if not unit:
            return False
        
        # Проверка: подразделение должно быть видимым
        if not self.can_view_unit(unit):
            return False
        
        # Проверка: подразделение должно иметь возможность иметь детей
        if not unit.unit_type.can_have_children:
            return False
        
        return True
    
    def get_available_parents_for_creation(self):
        """
        Получить список подразделений, в которых пользователь может создавать дочерние.
        
        Логика:
        - Пользователь может создавать в любом подразделении, которое:
          1. Находится в иерархии его подразделения (себя или потомки)
          2. Может иметь детей (can_have_children=True)
        """
        # Получаем все видимые подразделения (себя и всех потомков)
        visible_units = self.get_visible_units()
        
        # Фильтруем только те, которые могут иметь детей
        available_parents = visible_units.filter(
            unit_type__can_have_children=True
        )
        
        return available_parents
    
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
    
    # ========== РАСПИСАНИЯ ==========
    
    def get_visible_schedules(self):
        """
        Расписания, которые пользователь может видеть:
        - Свои расписания (где unit в расписании = своё подразделение)
        - Расписания дочерних подразделений
        """
        visible_units = self.get_visible_units()
        
        # Получаем все расписания, где подразделение в visible_units
        # TODO: нужно добавить связь между MonthlySchedule и Unit
        # Пока возвращаем пустой queryset
        return MonthlySchedule.objects.none()
    
    def can_view_schedule(self, schedule):
        """Может ли просматривать расписание"""
        # TODO: реализовать после добавления связи с Unit
        return True
    
    def can_edit_schedule(self, schedule):
        """Может ли редактировать расписание"""
        return schedule.created_by_id == self.user.id
    
    def can_delete_schedule(self, schedule):
        """Может ли удалять расписание"""
        return schedule.created_by_id == self.user.id
    
    # ========== ПЛАНЫ НА ДЕНЬ ==========
    
    def get_visible_day_plans(self):
        """
        Планы на день, которые пользователь может видеть
        """
        visible_units = self.get_visible_units()
        return DayPlan.objects.filter(unit__in=visible_units)
    
    def can_edit_day_plan(self, plan):
        """
        Может ли пользователь редактировать план на день
        """
        return plan.unit.id == self.user_unit.id or plan.created_by_id == self.user.id
    
    def can_delete_day_plan(self, plan):
        """
        Может ли пользователь удалять план на день
        """
        return plan.created_by_id == self.user.id
    
    # ========== НАЗНАЧЕНИЯ ==========
    
    def can_assign_person(self, day_plan, person):
        """
        Может ли пользователь назначить сотрудника на план дня
        """
        if day_plan.unit.id != self.user_unit.id:
            return False
        
        if person.unit.id != self.user_unit.id:
            return False
        
        if not person.clearances.filter(duty_type=day_plan.duty_type).exists():
            return False
        
        if person.exemptions.filter(
            date_from__lte=day_plan.date,
            date_to__gte=day_plan.date
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
        if hasattr(obj, 'unit'):
            return self.can_view_unit(obj.unit)
        return True
    
    def can_edit_object(self, obj):
        """Может ли редактировать объект"""
        if hasattr(obj, 'unit'):
            return self.can_edit_unit(obj.unit)
        return False
    
    def can_create_in_unit_by_id(self, unit_id):
        """Может ли создавать объекты в указанном подразделении (по ID)"""
        try:
            unit = Unit.objects.get(pk=unit_id)
            return self.can_create_in_unit(unit)
        except Unit.DoesNotExist:
            return False
    
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
        }