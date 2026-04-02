import calendar as cal
from datetime import datetime, date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Exists, OuterRef

from duty_plans.models import MonthlySchedule, DayPlan, DutyAssignment
from duty_types.models import DutyType
from people.models import Person
from users_app.access_service import AccessService


@login_required
def calendar(request):
    """Главная страница назначений - календарь"""
    print("\n" + "="*80)
    print("=== НАЧАЛО ОБРАБОТКИ КАЛЕНДАРЯ ===")
    
    access = AccessService(request.user)
    
    # Получаем месяц из GET или текущий
    today = datetime.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    print(f"Пользователь: {request.user} (id={request.user.id})")
    print(f"Подразделение пользователя: {access.user_unit.name} (id={access.user_unit.id})")
    print(f"Выбранный месяц: {year}-{month}")
    
    # Получаем расписание ТОЛЬКО для подразделения пользователя
    user_schedule = MonthlySchedule.objects.filter(
        month__year=year,
        month__month=month,
        unit=access.user_unit
    ).first()
    
    if not user_schedule:
        print(f"Нет расписания для подразделения {access.user_unit.name} на {year}-{month}")
        context = {
            'year': year,
            'month': month,
            'now_year': today.year,
            'now_month': today.month,
            'month_name': date(year, month, 1).strftime('%B %Y'),
            'calendar_data': [],
            'active_tab': 'assignments',
            'title': 'Назначения сотрудников',
        }
        return render(request, 'assignments/calendar.html', context)
    
    print(f"Найдено расписание: {user_schedule.name} для {access.user_unit.name}")
    
    # Получаем ВСЕ планы для этого расписания (включая планы дочерних подразделений)
    all_plans_for_unit = DayPlan.objects.filter(schedule=user_schedule)
    print(f"Всего планов в расписании: {all_plans_for_unit.count()}")
    
    for p in all_plans_for_unit:
        print(f"  План: id={p.id}, date={p.date}, type={p.type}, unit={p.unit.name}, duty={p.duty_type.name}, child_status={p.child_status}")
    
    # Показываем ВСЕ планы из расписания (включая дочерние подразделения)
    # Но с разным цветом в зависимости от статуса
    day_plans = DayPlan.objects.filter(
        schedule=user_schedule
    ).select_related('duty_type', 'unit').distinct()
    
    print(f"\nПЛАНОВ ДЛЯ ОТОБРАЖЕНИЯ (все планы расписания): {day_plans.count()}")
    
    for plan in day_plans:
        has_pending = plan.children.filter(child_status='pending').exists()
        has_assignments = plan.children.filter(assignments__isnull=False).exists()
        print(f"  ОТОБРАЖАЕМ: id={plan.id}, date={plan.date}, type={plan.type}, "
              f"unit={plan.unit.name}, duty={plan.duty_type.name}, "
              f"child_status={plan.child_status}, has_pending={has_pending}, has_assignments={has_assignments}")
    
    # Строим календарь
    calendar_data = build_calendar_data(day_plans, year, month, access)
    
    # Группируем по неделям
    weeks = []
    current_week = []
    for day_data in calendar_data:
        if day_data['date'].weekday() == 0 and current_week:
            weeks.append(current_week)
            current_week = []
        current_week.append(day_data)
    if current_week:
        weeks.append(current_week)
    
    context = {
        'year': year,
        'month': month,
        'now_year': today.year,
        'now_month': today.month,
        'month_name': date(year, month, 1).strftime('%B %Y'),
        'calendar_data': weeks,
        'active_tab': 'assignments',
        'title': 'Назначения сотрудников',
    }
    
    print("=== КАЛЕНДАРЬ ПОСТРОЕН ===")
    print("="*80 + "\n")
    
    return render(request, 'assignments/calendar.html', context)


def build_calendar_data(day_plans, year, month, access):
    """Строит данные для календаря"""
    # Дни месяца
    last_day = cal.monthrange(year, month)[1]
    dates = [date(year, month, day) for day in range(1, last_day + 1)]
    
    # Группируем планы по дате
    plans_by_date = {}
    for plan in day_plans:
        if plan.date not in plans_by_date:
            plans_by_date[plan.date] = []
        plans_by_date[plan.date].append(plan)
    
    # Строим календарь
    calendar_data = []
    for day in dates:
        day_data = {
            'date': day,
            'weekday': day.strftime('%a'),
            'plans': []
        }
        
        # Получаем планы на этот день
        plans = plans_by_date.get(day, [])
        
        for plan in plans:
            required = plan.duty_type.required_people
            
            # Определяем, чей это план (своего подразделения или дочернего)
            is_own_unit = (plan.unit.id == access.user_unit.id)
            
            # Получаем назначения
            assignments = None
            assignments_count = 0
            
            if is_own_unit:
                # Свой план - берем назначения напрямую
                assignments = plan.assignments.select_related('person', 'person__rank')
                assignments_count = assignments.count()
            else:
                # План дочернего подразделения - нужно получить назначения из дочерних планов
                # Ищем все дочерние планы этого плана (прямые или через цепочку)
                child_plans = plan.children.all()
                if child_plans.exists():
                    # Берем назначения из первого дочернего плана (или объединяем)
                    # В данном случае структура: родитель -> дочерний план -> назначения
                    # Например: план Ф1 (id=136) -> план incoming (id=137) -> назначения
                    for child_plan in child_plans:
                        child_assignments = child_plan.assignments.select_related('person', 'person__rank')
                        if child_assignments.exists():
                            assignments = child_assignments
                            assignments_count = child_assignments.count()
                            break
            
            # Если назначений нет, создаем пустой queryset
            if assignments is None:
                assignments = []
            
            # Проверяем, есть ли дочерние планы
            has_children = plan.children.exists()
            child_is_pending = plan.children.filter(child_status='pending').exists()
            child_has_assignments = plan.children.filter(assignments__isnull=False).exists()
            
            # Определяем статус и цвет
            if not is_own_unit:
                # Это план дочернего подразделения - показываем статус в зависимости от наличия назначений
                if assignments_count > 0:
                    if assignments_count >= required:
                        status = 'completed'
                        status_text = f'✅ Полностью назначен ({assignments_count}/{required})'
                    else:
                        status = 'partial'
                        status_text = f'🔄 Частично назначен ({assignments_count}/{required})'
                elif child_is_pending:
                    status = 'delegated'
                    status_text = '📎 Делегирован дочернему подразделению (ожидает назначения)'
                else:
                    status = 'delegated'
                    status_text = '📎 Делегирован дочернему подразделению'
            elif plan.type == 'incoming' and has_children and child_is_pending:
                # Свой входящий наряд, у которого есть дочерний в статусе pending - делегирован
                status = 'delegated'
                status_text = '📎 Делегирован дочернему подразделению (ожидает назначения)'
            elif assignments_count == 0:
                status = 'unassigned'
                status_text = '⚠️ Требуется назначение'
            elif assignments_count >= required:
                status = 'completed'
                status_text = f'✅ Полностью назначен ({assignments_count}/{required})'
            else:
                status = 'partial'
                status_text = f'🔄 Частично назначен ({assignments_count}/{required})'
            
            # Отображаем название подразделения
            unit_display = plan.unit.name if plan.unit else 'Без подразделения'
            
            # Если это не свое подразделение, добавляем пометку
            if not is_own_unit:
                unit_display = f'📎 {unit_display} (дочернее)'
            elif plan.type == 'incoming' and plan.parent:
                unit_display = f'📎 {unit_display} (от {plan.parent.unit.name})'
            
            # Формируем список назначенных сотрудников для отображения
            assigned_people = []
            for a in assignments:
                assigned_people.append({
                    'id': a.id,
                    'person': a.person,
                    'full_name': a.person.full_name(),
                    'last_name': a.person.last_name,
                    'rank_name': a.person.rank.name if a.person.rank else '',
                    'unit_name': a.person.unit.name,
                })
            
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
                'is_delegated': not is_own_unit or (plan.type == 'incoming' and child_is_pending),
            })
        
        # Сортируем планы в ячейке: сначала те, что требуют назначения
        day_data['plans'].sort(key=lambda x: (x['status'] != 'unassigned', x['duty_name']))
        
        calendar_data.append(day_data)
    
    return calendar_data


@login_required
def get_available_people(request, plan_id):
    """Получить доступных сотрудников (AJAX)"""
    plan = get_object_or_404(DayPlan, pk=plan_id)
    access = AccessService(request.user)
    
    print(f"\n=== get_available_people для плана {plan_id} ===")
    print(f"План: type={plan.type}, unit={plan.unit.name}, duty={plan.duty_type.name}")
    
    if not access.can_edit_day_plan(plan):
        print(f"Нет прав на редактирование плана {plan_id}")
        return JsonResponse({'error': 'Нет прав'}, status=403)
    
    # Проверяем, можно ли назначать:
    # 1. Если план не своего подразделения - нельзя
    if plan.unit.id != access.user_unit.id:
        print(f"План {plan_id} принадлежит другому подразделению, нельзя назначать")
        return JsonResponse({'error': 'Наряд делегирован дочернему подразделению'}, status=400)
    
    # 2. Если есть дочерние планы в статусе pending - нельзя (делегирован дальше)
    has_pending_children = plan.children.filter(child_status='pending').exists()
    if has_pending_children:
        print(f"План {plan_id} имеет дочерние планы в статусе pending, нельзя назначать")
        return JsonResponse({'error': 'Наряд делегирован дочернему подразделению'}, status=400)
    
    # Все сотрудники подразделения
    all_people = Person.objects.filter(unit=plan.unit).select_related('rank')
    
    # Фильтруем по допускам
    cleared = Person.objects.filter(
        unit=plan.unit,
        clearances__duty_type=plan.duty_type
    ).distinct()
    
    # Фильтруем по освобождениям
    exempted = Person.objects.filter(
        exemptions__date_from__lte=plan.date,
        exemptions__date_to__gte=plan.date
    ).distinct()
    
    # Уже назначенные
    assigned_ids = plan.assignments.values_list('person_id', flat=True)
    
    # Доступные
    available = cleared.exclude(id__in=assigned_ids).exclude(id__in=exempted)
    
    print(f"Всего сотрудников: {all_people.count()}")
    print(f"Допущенных: {cleared.count()}")
    print(f"Освобожденных: {exempted.count()}")
    print(f"Уже назначенных: {len(assigned_ids)}")
    print(f"Доступных: {available.count()}")
    
    # Недоступные
    unavailable = []
    for person in all_people:
        if person.id in assigned_ids:
            unavailable.append({'id': person.id, 'name': person.full_name(), 'rank': person.rank.name, 'reason': 'Уже назначен'})
        elif person.id in exempted:
            unavailable.append({'id': person.id, 'name': person.full_name(), 'rank': person.rank.name, 'reason': 'Освобожден'})
        elif person.id not in cleared:
            unavailable.append({'id': person.id, 'name': person.full_name(), 'rank': person.rank.name, 'reason': 'Нет допуска'})
    
    data = {
        'plan_id': plan.id,
        'duty_name': plan.duty_type.name,
        'unit_name': plan.unit.name,
        'date': plan.date.strftime('%d.%m.%Y'),
        'required_people': plan.duty_type.required_people,
        'current_count': plan.assignments.count(),
        'available': [{'id': p.id, 'name': p.full_name(), 'rank': p.rank.name} for p in available],
        'assigned': [{'id': a.id, 'name': a.person.full_name(), 'rank': a.person.rank.name} for a in plan.assignments.select_related('person', 'person__rank')],
        'unavailable': unavailable,
    }
    
    print("=== Данные отправлены ===")
    return JsonResponse(data)


@login_required
def assign_person(request, plan_id):
    """Назначить сотрудника"""
    plan = get_object_or_404(DayPlan, pk=plan_id)
    person_id = request.POST.get('person_id')
    
    if not person_id:
        messages.error(request, 'Сотрудник не выбран')
        return redirect('assignment:calendar')
    
    person = get_object_or_404(Person, pk=person_id)
    access = AccessService(request.user)
    
    if not access.can_edit_day_plan(plan):
        messages.error(request, 'Нет прав на назначение')
        return redirect('assignment:calendar')
    
    # Проверяем, можно ли назначать:
    # 1. Если план не своего подразделения - нельзя
    if plan.unit.id != access.user_unit.id:
        messages.error(request, 'Наряд делегирован дочернему подразделению')
        return redirect('assignment:calendar')
    
    # 2. Если есть дочерние планы в статусе pending - нельзя (делегирован дальше)
    has_pending_children = plan.children.filter(child_status='pending').exists()
    if has_pending_children:
        messages.error(request, 'Наряд делегирован дочернему подразделению')
        return redirect('assignment:calendar')
    
    if person.unit != plan.unit:
        messages.error(request, 'Сотрудник не из этого подразделения')
        return redirect('assignment:calendar')
    
    if not person.clearances.filter(duty_type=plan.duty_type).exists():
        messages.error(request, f'Сотрудник {person.full_name()} не имеет допуска к этому типу наряда')
        return redirect('assignment:calendar')
    
    if person.exemptions.filter(date_from__lte=plan.date, date_to__gte=plan.date).exists():
        messages.error(request, f'Сотрудник {person.full_name()} освобожден в этот день')
        return redirect('assignment:calendar')
    
    if plan.assignments.count() >= plan.duty_type.required_people:
        messages.error(request, f'Превышен лимит назначений (максимум {plan.duty_type.required_people} чел.)')
        return redirect('assignment:calendar')
    
    _, created = DutyAssignment.objects.get_or_create(
        day_plan=plan,
        person=person,
        defaults={'assigned_by': request.user}
    )
    
    if created:
        messages.success(request, f'Сотрудник {person.full_name()} назначен')
    else:
        messages.warning(request, f'Сотрудник {person.full_name()} уже назначен')
    
    return redirect(f"{request.GET.get('next', '/assignments/')}?year={plan.date.year}&month={plan.date.month}")


@login_required
def unassign_person(request, assignment_id):
    """Снять назначение"""
    assignment = get_object_or_404(DutyAssignment, pk=assignment_id)
    access = AccessService(request.user)
    
    plan = assignment.day_plan
    
    if not access.can_edit_day_plan(plan):
        messages.error(request, 'Нет прав на снятие назначения')
        return redirect('assignment:calendar')
    
    person_name = assignment.person.full_name()
    assignment.delete()
    messages.success(request, f'Назначение сотрудника {person_name} снято')
    
    return redirect(f"{request.GET.get('next', '/assignments/')}?year={plan.date.year}&month={plan.date.month}")