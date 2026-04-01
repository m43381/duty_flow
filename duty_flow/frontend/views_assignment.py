import calendar as cal  # Переименовываем импорт
from datetime import datetime, date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q

from duty_plans.models import MonthlySchedule, DayPlan, DutyAssignment
from duty_types.models import DutyType
from people.models import Person
from users_app.access_service import AccessService


@login_required
def calendar(request):
    """Главная страница назначений - календарь"""
    access = AccessService(request.user)
    
    # Получаем месяц из GET или текущий
    today = datetime.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    # Получаем все видимые подразделения
    visible_units = access.get_visible_units()
    
    # Получаем все расписания на выбранный месяц
    schedules = MonthlySchedule.objects.filter(
        month__year=year,
        month__month=month,
        unit__in=visible_units
    ).select_related('unit')
    
    # Получаем все планы на день
    day_plans = DayPlan.objects.filter(
        schedule__in=schedules,
        type='own',
        child_status='none'
    ).select_related('duty_type', 'unit', 'schedule')
    
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
    
    return render(request, 'assignments/calendar.html', context)


def build_calendar_data(day_plans, year, month, access):
    """Строит данные для календаря"""
    # Используем cal вместо calendar
    last_day = cal.monthrange(year, month)[1]
    dates = [date(year, month, day) for day in range(1, last_day + 1)]
    
    # Получаем все типы нарядов
    all_duty_types = DutyType.objects.all().order_by('name')
    
    # Группируем планы
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
                assignments = plan.assignments.select_related('person', 'person__rank')
                assignments_count = assignments.count()
                
                if assignments_count == 0:
                    status = 'unassigned'
                    status_text = 'Требуется назначение'
                else:
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
                    'duty_name': duty.name,
                    'required_people': duty.required_people,
                    'unit_name': plan.unit.name,
                    'status': status,
                    'status_text': status_text,
                    'assignments': assignments,
                })
            else:
                day_data['plans'].append({
                    'plan_id': None,
                    'duty_name': duty.name,
                    'required_people': duty.required_people,
                    'unit_name': None,
                    'status': 'no_plan',
                    'status_text': 'Нет плана',
                    'assignments': [],
                })
        
        calendar_data.append(day_data)
    
    return calendar_data


@login_required
def get_available_people(request, plan_id):
    """Получить доступных сотрудников (AJAX)"""
    plan = get_object_or_404(DayPlan, pk=plan_id)
    access = AccessService(request.user)
    
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
    
    # Доступные
    available = cleared.exclude(id__in=assigned_ids).exclude(id__in=exempted)
    
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
        'required_people': plan.duty_type.required_people,
        'current_count': plan.assignments.count(),
        'available': [{'id': p.id, 'name': p.full_name(), 'rank': p.rank.name} for p in available],
        'assigned': [{'id': a.id, 'name': a.person.full_name(), 'rank': a.person.rank.name} for a in plan.assignments.select_related('person', 'person__rank')],
        'unavailable': unavailable,
    }
    
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
    
    if person.unit != plan.unit:
        messages.error(request, 'Сотрудник не из этого подразделения')
        return redirect('assignment:calendar')
    
    if not person.clearances.filter(duty_type=plan.duty_type).exists():
        messages.error(request, f'Сотрудник {person.full_name()} не имеет допуска')
        return redirect('assignment:calendar')
    
    if person.exemptions.filter(date_from__lte=plan.date, date_to__gte=plan.date).exists():
        messages.error(request, f'Сотрудник {person.full_name()} освобожден')
        return redirect('assignment:calendar')
    
    if plan.assignments.count() >= plan.duty_type.required_people:
        messages.error(request, 'Превышен лимит назначений')
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