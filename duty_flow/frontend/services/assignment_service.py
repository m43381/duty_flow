"""
Сервис для работы с назначениями на наряды
"""
import calendar as cal
from datetime import date
from django.db.models import Q
from duty_plans.models import MonthlySchedule, DayPlan, DutyAssignment
from people.models import Person


class AssignmentService:
    """Сервис для работы с назначениями"""
    
    @staticmethod
    def get_user_schedule(user_unit, year, month):
        """Получает расписание для подразделения пользователя на указанный месяц"""
        return MonthlySchedule.objects.filter(
            month__year=year,
            month__month=month,
            unit=user_unit
        ).first()
    
    @staticmethod
    def build_calendar_data(day_plans, year, month, user_unit):
        """Строит данные для календаря назначений"""
        last_day = cal.monthrange(year, month)[1]
        dates = [date(year, month, day) for day in range(1, last_day + 1)]
        
        # Группируем планы по дате
        plans_by_date = {}
        for plan in day_plans:
            if plan.date not in plans_by_date:
                plans_by_date[plan.date] = []
            plans_by_date[plan.date].append(plan)
        
        calendar_data = []
        for day in dates:
            day_data = {
                'date': day,
                'weekday': day.strftime('%a'),
                'plans': []
            }
            
            plans = plans_by_date.get(day, [])
            
            for plan in plans:
                required = plan.duty_type.required_people
                is_own_unit = (plan.unit.id == user_unit.id)
                
                # Получаем назначения
                assignments, assignments_count = AssignmentService.get_plan_assignments(plan, is_own_unit)
                
                # Определяем статус
                status, status_text = AssignmentService.get_plan_status(
                    plan, is_own_unit, assignments_count, required
                )
                
                unit_display = AssignmentService.get_unit_display(plan, is_own_unit)
                
                assigned_people = AssignmentService.format_assigned_people(assignments)
                
                day_data['plans'].append({
                    'plan_id': plan.id,
                    'duty_name': plan.duty_type.name,
                    'required_people': required,
                    'unit_name': unit_display,
                    'unit_id': plan.unit.id if plan.unit else None,
                    'plan_type': plan.type,
                    'status': status,
                    'status_text': status_text,
                    'assignments': assigned_people,
                    'assigned_count': assignments_count,
                    'is_own_unit': is_own_unit,
                    'is_delegated': AssignmentService.is_plan_delegated(plan, is_own_unit),
                })
            
            # Сортируем планы: сначала требующие назначения
            day_data['plans'].sort(key=lambda x: (x['status'] != 'unassigned', x['duty_name']))
            calendar_data.append(day_data)
        
        return calendar_data
    
    @staticmethod
    def get_plan_assignments(plan, is_own_unit):
        """Возвращает назначения для плана"""
        if is_own_unit:
            assignments = plan.assignments.select_related('person', 'person__rank')
            return assignments, assignments.count()
        else:
            # План дочернего подразделения - ищем назначения в дочерних планах
            for child_plan in plan.children.all():
                child_assignments = child_plan.assignments.select_related('person', 'person__rank')
                if child_assignments.exists():
                    return child_assignments, child_assignments.count()
            return [], 0
    
    @staticmethod
    def get_plan_status(plan, is_own_unit, assignments_count, required):
        """Определяет статус плана и текст статуса"""
        has_children = plan.children.exists()
        child_is_pending = plan.children.filter(child_status='pending').exists()
        
        if not is_own_unit:
            if assignments_count > 0:
                if assignments_count >= required:
                    return 'completed', f'✅ Полностью назначен ({assignments_count}/{required})'
                return 'partial', f'🔄 Частично назначен ({assignments_count}/{required})'
            return 'delegated', '📎 Делегирован дочернему подразделению'
        
        if plan.type == 'incoming' and has_children and child_is_pending:
            return 'delegated', '📎 Делегирован дочернему подразделению (ожидает назначения)'
        
        if assignments_count == 0:
            return 'unassigned', '⚠️ Требуется назначение'
        
        if assignments_count >= required:
            return 'completed', f'✅ Полностью назначен ({assignments_count}/{required})'
        
        return 'partial', f'🔄 Частично назначен ({assignments_count}/{required})'
    
    @staticmethod
    def get_unit_display(plan, is_own_unit):
        """Форматирует отображение подразделения"""
        if not is_own_unit:
            return f'📎 {plan.unit.name} (дочернее)'
        if plan.type == 'incoming' and plan.parent:
            return f'📎 {plan.unit.name} (от {plan.parent.unit.name})'
        return plan.unit.name
    
    @staticmethod
    def is_plan_delegated(plan, is_own_unit):
        """Проверяет, делегирован ли план"""
        if not is_own_unit:
            return True
        child_is_pending = plan.children.filter(child_status='pending').exists()
        return plan.type == 'incoming' and child_is_pending
    
    @staticmethod
    def format_assigned_people(assignments):
        """Форматирует список назначенных сотрудников для отображения"""
        result = []
        for a in assignments:
            result.append({
                'id': a.id,
                'person': a.person,
                'full_name': a.person.full_name(),
                'last_name': a.person.last_name,
                'rank_name': a.person.rank.name if a.person.rank else '',
                'unit_name': a.person.unit.name,
            })
        return result
    
    @staticmethod
    def get_available_people_for_plan(plan, user_unit):
        """
        Возвращает доступных сотрудников для назначения на план
        Возвращает: available, assigned, unavailable
        """
        all_people = Person.objects.filter(unit=plan.unit).select_related('rank')
        
        # Допущенные к типу наряда
        cleared = Person.objects.filter(
            unit=plan.unit,
            clearances__duty_type=plan.duty_type
        ).distinct()
        
        # Освобожденные в этот день
        exempted = Person.objects.filter(
            exemptions__date_from__lte=plan.date,
            exemptions__date_to__gte=plan.date
        ).distinct()
        
        # Уже назначенные
        assigned_ids = plan.assignments.values_list('person_id', flat=True)
        
        # Доступные
        available = cleared.exclude(id__in=assigned_ids).exclude(id__in=exempted)
        
        # Недоступные с причинами
        unavailable = []
        for person in all_people:
            if person.id in assigned_ids:
                unavailable.append({'id': person.id, 'name': person.full_name(), 'rank': person.rank.name, 'reason': 'Уже назначен'})
            elif person.id in exempted:
                unavailable.append({'id': person.id, 'name': person.full_name(), 'rank': person.rank.name, 'reason': 'Освобожден'})
            elif person.id not in cleared:
                unavailable.append({'id': person.id, 'name': person.full_name(), 'rank': person.rank.name, 'reason': 'Нет допуска'})
        
        return available, assigned_ids, unavailable
    
    @staticmethod
    def can_assign_to_plan(plan, user_unit, person):
        """Проверяет, можно ли назначить конкретного сотрудника на план"""
        # Проверка подразделения
        if person.unit != plan.unit:
            return False, 'Сотрудник не из этого подразделения'
        
        # Проверка допуска
        if not person.clearances.filter(duty_type=plan.duty_type).exists():
            return False, f'Сотрудник не имеет допуска к этому типу наряда'
        
        # Проверка освобождения
        if person.exemptions.filter(date_from__lte=plan.date, date_to__gte=plan.date).exists():
            return False, f'Сотрудник освобожден в этот день'
        
        # Проверка лимита
        if plan.assignments.count() >= plan.duty_type.required_people:
            return False, f'Превышен лимит назначений (максимум {plan.duty_type.required_people} чел.)'
        
        return True, ''
    
    @staticmethod
    def can_edit_plan(plan, user_unit):
        """Проверяет, можно ли редактировать план (назначать/снимать)"""
        # План не своего подразделения
        if plan.unit.id != user_unit.id:
            return False, 'Наряд делегирован дочернему подразделению'
        
        # Есть дочерние планы в статусе pending
        if plan.children.filter(child_status='pending').exists():
            return False, 'Наряд делегирован дочернему подразделению'
        
        return True, ''