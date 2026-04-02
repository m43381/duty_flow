from django.db import models
from units.models import Unit
from duty_plans.models import MonthlySchedule, DayPlan
from duty_types.models import DutyType


class AccessService:
    """
    Универсальный сервис для проверки прав доступа
    Основан на иерархии подразделений
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
            return Unit.objects.all()
        else:
            editable_ids = [self.user_unit.id]
            for child in self.user_unit.children.all():
                editable_ids.append(child.id)
            return Unit.objects.filter(id__in=editable_ids)
    
    def can_view_unit(self, unit):
        """Может ли просматривать подразделение"""
        if self.user_level == 0:
            return True
        return unit.id in self.user_unit.get_descendants_ids(include_self=True)
    
    def can_edit_unit(self, unit):
        """Может ли редактировать подразделение"""
        if self.user_level == 0:
            return True
        
        if unit.id == self.user_unit.id:
            return True
        
        if unit.parent and unit.parent.id == self.user_unit.id:
            return True
        
        return False
    
    def can_delete_unit(self, unit):
        """Может ли удалять подразделение"""
        if self.user_level == 0:
            return True
        
        if unit.id == self.user_unit.id:
            return False
        
        if unit.parent and unit.parent.id == self.user_unit.id:
            return True
        
        return False
    
    def can_create_in_unit(self, unit):
        """Может ли создавать дочерние подразделения в указанном подразделении"""
        if not unit:
            return False
        
        if not self.can_view_unit(unit):
            return False
        
        if not unit.unit_type.can_have_children:
            return False
        
        if self.user_level == 0:
            return True
        
        return unit.id == self.user_unit.id
    
    def get_available_parents_for_creation(self):
        """Список подразделений, в которых можно создавать дочерние"""
        if self.user_level == 0:
            return Unit.objects.filter(unit_type__can_have_children=True)
        else:
            if self.user_unit.unit_type.can_have_children:
                return Unit.objects.filter(id=self.user_unit.id)
            return Unit.objects.none()
    
    # ========== ПОЛЬЗОВАТЕЛИ ==========
    
    def get_visible_users(self):
        """
        Все пользователи, которых может видеть:
        - Себя
        - Пользователей своего подразделения
        - Пользователей всех дочерних подразделений (любой глубины)
        """
        from django.contrib.auth.models import User
        
        visible_units = self.get_visible_units()
        return User.objects.filter(profile__unit__in=visible_units).select_related('profile')
    
    def can_create_user_for_unit(self, target_unit):
        """
        Может ли создать пользователя для подразделения:
        - Свое подразделение (помощник)
        - Прямое дочернее (руководитель)
        """
        if not target_unit:
            return False
        
        # Свое подразделение
        if target_unit.id == self.user_unit.id:
            return True
        
        # Прямое дочернее
        if target_unit.parent and target_unit.parent.id == self.user_unit.id:
            return True
        
        return False
    
    def can_edit_user(self, target_user):
        """
        Может ли редактировать пользователя:
        - Себя
        - Пользователей своего подразделения
        """
        if target_user.id == self.user.id:
            return True
        
        target_unit = target_user.profile.unit
        return target_unit.id == self.user_unit.id
    
    def can_delete_user(self, target_user):
        """
        Может ли удалять пользователя:
        - Пользователей своего подразделения (помощников)
        - Пользователей прямых дочерних подразделений (руководителей)
        """
        # Нельзя удалить себя
        if target_user.id == self.user.id:
            return False
        
        target_unit = target_user.profile.unit
        
        # Свое подразделение - можно удалять (помощников)
        if target_unit.id == self.user_unit.id:
            return True
        
        # Прямое дочернее - можно удалять (руководителей)
        if target_unit.parent and target_unit.parent.id == self.user_unit.id:
            return True
        
        return False
    
    def can_change_password(self, target_user):
        """
        Может ли менять пароль пользователя:
        - Себе
        - Пользователям своего подразделения
        """
        if target_user.id == self.user.id:
            return True
        
        target_unit = target_user.profile.unit
        return target_unit.id == self.user_unit.id
    
    # ========== ТИПЫ НАРЯДОВ ==========
    
    def get_available_duty_types(self):
        """Типы нарядов, доступные для планирования"""
        own_types = DutyType.objects.filter(unit=self.user_unit)
        
        parent_types = DutyType.objects.none()
        if self.user_unit.parent:
            parent_types = DutyType.objects.filter(unit=self.user_unit.parent)
        
        return (own_types | parent_types).distinct()
    
    # ========== РАСПИСАНИЯ ==========
    
    def get_visible_schedules(self):
        """Расписания, которые пользователь может видеть"""
        visible_units = self.get_visible_units()
        return MonthlySchedule.objects.filter(unit__in=visible_units)
    
    def can_view_schedule(self, schedule):
        """Может ли просматривать расписание"""
        return self.can_view_unit(schedule.unit)
    
    def can_edit_schedule(self, schedule):
        """Может ли редактировать расписание"""
        # Можно редактировать расписания своего подразделения
        if schedule.unit.id == self.user_unit.id:
            return True
        
        # Если есть поле created_by, проверяем
        if hasattr(schedule, 'created_by_id') and schedule.created_by_id == self.user.id:
            return True
        
        return False
    
    def can_delete_schedule(self, schedule):
        """Может ли удалять расписание"""
        # Аналогично редактированию
        if schedule.unit.id == self.user_unit.id:
            return True
        
        if hasattr(schedule, 'created_by_id') and schedule.created_by_id == self.user.id:
            return True
        
        return False
    
    # ========== ПЛАНЫ НА ДЕНЬ ==========
    
    def get_visible_day_plans(self):
        """Планы на день, которые пользователь может видеть"""
        visible_units = self.get_visible_units()
        return DayPlan.objects.filter(unit__in=visible_units)
    
    def can_edit_day_plan(self, plan):
        """
        Может ли редактировать план на день
        У DayPlan нет поля created_by, поэтому проверяем только по подразделению
        """
        # Можно редактировать только планы своего подразделения
        return plan.unit.id == self.user_unit.id
    
    def can_delete_day_plan(self, plan):
        """
        Может ли удалять план на день
        У DayPlan нет поля created_by, поэтому проверяем только по подразделению
        """
        # Можно удалять только планы своего подразделения
        return plan.unit.id == self.user_unit.id
    
    # ========== НАЗНАЧЕНИЯ ==========
    
    def can_assign_person(self, day_plan, person):
        """Может ли назначить сотрудника на план дня"""
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
        if hasattr(obj, 'unit'):
            return self.can_view_unit(obj.unit)
        return True
    
    def can_edit_object(self, obj):
        if hasattr(obj, 'unit'):
            return self.can_edit_unit(obj.unit)
        return False
    
    def can_delete_object(self, obj):
        if hasattr(obj, 'unit'):
            return self.can_delete_unit(obj.unit)
        return False
    
    def can_create_in_unit_by_id(self, unit_id):
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
        return {
            'available_units': self.get_visible_units(),
            'available_duty_types': self.get_available_duty_types(),
            'can_create_plan': self.can_create_plan(),
        }
    
    def can_create_plan(self):
        """Может ли создавать расписания"""
        # Создавать расписания может любое подразделение
        return True