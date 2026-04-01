import calendar
from datetime import datetime, date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q

from duty_plans.models import MonthlySchedule, DayPlan, DutyAssignment
from duty_types.models import DutyType
from people.models import Person
from units.models import Unit
from users_app.access_service import AccessService


@login_required
def calendar(request):
    """Главная страница назначений - календарь"""
    access = AccessService(request.user)
    
    # Получаем месяц из GET или текущий
    today = datetime.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    # Получаем все видимые подразделения (для всех пользователей)
    visible_units = access.get_visible_units()
    
    # Получаем все расписания на выбранный месяц для видимых подразделений
    schedules = MonthlySchedule.objects.filter(
        month__year=year,
        month__month=month,
        unit__in=visible_units
    ).select_related('unit')
    
    # Получаем все планы на день для этих расписаний
    day_plans = DayPlan.objects.filter(
        schedule__in=schedules,
        type='own',
        child_status='none'
    ).select_related('duty_type', 'unit', 'schedule')
    
    # Строим календарь
    calendar_data = build_calendar_data(day_plans, year, month, access)
    
    context = {
        'year': year,
        'month': month,
        'month_name': date(year, month, 1).strftime('%B %Y'),
        'calendar_data': calendar_data,
        'active_tab': 'assignments',
        'title': 'Назначения сотрудников',
    }
    
    return render(request, 'assignments/calendar.html', context)


def build_calendar_data(day_plans, year, month, access):
    """Строит данные для календаря"""
    # Дни месяца
    last_day = calendar.monthrange(year, month)[1]
    dates = [date(year, month, day) for day in range(1, last_day + 1)]
    
    # Получаем все типы нарядов
    all_duty_types = DutyType.objects.all().order_by('name')
    
    # Группируем планы по дате и типу наряда
    plans_dict = {}
    for plan in day_plans:
        key = (plan.date, plan.duty_type_id)
        plans_dict[key] = plan
    
    # Строим календарь
    calendar_data = []
    for day in dates:
        day_data = {
            'date': day,
            'weekday': day.strftime('%a'),
            'plans': []
        }
        
        for duty in all_duty_types:
            plan = plans_dict.get((day, duty.id))
            
            if plan:
                # Получаем назначения
                assignments = plan.assignments.select_related('person', 'person__rank')
                assignments_count = assignments.count()
                
                # Определяем статус
                if assignments_count == 0:
                    status = 'unassigned'
                    status_text = 'Требуется назначение'
                else:
                    # Проверяем, из какого подразделения назначенные
                    own_count = assignments.filter(person__unit=plan.unit).count()
                    child_count = assignments.filter(~Q(person__unit=plan.unit)).count()
                    
                    if own_count > 0:
                        status = 'assigned_own'
                        status_text = f'Назначено: {assignments_count} чел. (из своего)'
                    elif child_count > 0:
                        status = 'assigned_child'
                        status_text = f'Назначено: {assignments_count} чел. (из дочерних)'
                    else:
                        status = 'assigned'
                        status_text = f'Назначено: {assignments_count} чел.'
                
                day_data['plans'].append({
                    'plan_id': plan.id,
                    'duty_id': duty.id,
                    'duty_name': duty.name,
                    'required_people': duty.required_people,
                    'unit_id': plan.unit_id,
                    'unit_name': plan.unit.name,
                    'status': status,
                    'status_text': status_text,
                    'assignments': assignments,
                    'can_assign': access.can_edit_day_plan(plan),  # Проверка прав
                })
            else:
                day_data['plans'].append({
                    'plan_id': None,
                    'duty_id': duty.id,
                    'duty_name': duty.name,
                    'required_people': duty.required_people,
                    'unit_id': None,
                    'unit_name': None,
                    'status': 'no_plan',
                    'status_text': 'Нет плана',
                    'assignments': [],
                    'can_assign': False,
                })
        
        calendar_data.append(day_data)
    
    return calendar_data


@login_required
def get_available_people(request, plan_id):
    """Получить доступных сотрудников для назначения (AJAX)"""
    plan = get_object_or_404(DayPlan, pk=plan_id)
    access = AccessService(request.user)
    
    # Проверка прав: можно назначать только если есть право редактировать план
    if not access.can_edit_day_plan(plan):
        return JsonResponse({'error': 'Нет прав'}, status=403)
    
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
    
    # Доступные для назначения
    available = cleared.exclude(id__in=assigned_ids).exclude(id__in=exempted)
    
    # Недоступные по причине
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
        'required_people': plan.duty_type.required_people,
        'current_count': plan.assignments.count(),
        'available': [
            {'id': p.id, 'name': p.full_name(), 'rank': p.rank.name}
            for p in available
        ],
        'assigned': [
            {'id': a.id, 'person_id': a.person_id, 'name': a.person.full_name(), 'rank': a.person.rank.name}
            for a in plan.assignments.select_related('person', 'person__rank')
        ],
        'unavailable': unavailable,
    }
    
    return JsonResponse(data)


@login_required
def assign_person(request, plan_id):
    """Назначить сотрудника на план"""
    plan = get_object_or_404(DayPlan, pk=plan_id)
    person_id = request.POST.get('person_id')
    
    if not person_id:
        messages.error(request, 'Сотрудник не выбран')
        return redirect('assignment:calendar')
    
    person = get_object_or_404(Person, pk=person_id)
    access = AccessService(request.user)
    
    # Проверка прав
    if not access.can_edit_day_plan(plan):
        messages.error(request, 'Нет прав на назначение')
        return redirect('assignment:calendar')
    
    # Проверка: сотрудник из того же подразделения
    if person.unit != plan.unit:
        messages.error(request, 'Сотрудник не из этого подразделения')
        return redirect('assignment:calendar')
    
    # Проверка допуска
    if not person.clearances.filter(duty_type=plan.duty_type).exists():
        messages.error(request, f'Сотрудник {person.full_name()} не имеет допуска к этому типу наряда')
        return redirect('assignment:calendar')
    
    # Проверка освобождения
    if person.exemptions.filter(
        date_from__lte=plan.date,
        date_to__gte=plan.date
    ).exists():
        messages.error(request, f'Сотрудник {person.full_name()} освобожден в этот день')
        return redirect('assignment:calendar')
    
    # Проверка лимита
    if plan.assignments.count() >= plan.duty_type.required_people:
        messages.error(request, f'Превышен лимит назначений (максимум {plan.duty_type.required_people} чел.)')
        return redirect('assignment:calendar')
    
    # Создаем назначение
    assignment, created = DutyAssignment.objects.get_or_create(
        day_plan=plan,
        person=person,
        defaults={'assigned_by': request.user}
    )
    
    if created:
        messages.success(request, f'Сотрудник {person.full_name()} назначен')
    else:
        messages.warning(request, f'Сотрудник {person.full_name()} уже назначен')
    
    # Возвращаемся на календарь с сохранением месяца
    return redirect(f"{request.GET.get('next', '/assignments/')}?year={plan.date.year}&month={plan.date.month}")


@login_required
def unassign_person(request, assignment_id):
    """Снять назначение сотрудника"""
    assignment = get_object_or_404(DutyAssignment, pk=assignment_id)
    access = AccessService(request.user)
    
    plan = assignment.day_plan
    
    if not access.can_edit_day_plan(plan):
        messages.error(request, 'Нет прав на снятие назначения')
        return redirect('assignment:calendar')
    
    person_name = assignment.person.full_name()
    assignment.delete()
    
    messages.success(request, f'Назначение сотрудника {person_name} снято')
    
    # Возвращаемся на календарь с сохранением месяца
    return redirect(f"{request.GET.get('next', '/assignments/')}?year={plan.date.year}&month={plan.date.month}")