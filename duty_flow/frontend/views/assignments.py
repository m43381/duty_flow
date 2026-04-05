from datetime import datetime, date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from duty_plans.models import DayPlan, DutyAssignment
from people.models import Person
from users_app.access_service import AccessService
from frontend.services.assignment_service import AssignmentService


@login_required
def calendar(request):
    """Главная страница назначений - календарь"""
    access = AccessService(request.user)
    
    today = datetime.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    # Получаем расписание для подразделения пользователя
    user_schedule = AssignmentService.get_user_schedule(access.user_unit, year, month)
    
    if not user_schedule:
        return render(request, 'assignments/calendar.html', {
            'year': year,
            'month': month,
            'now_year': today.year,
            'now_month': today.month,
            'month_name': date(year, month, 1).strftime('%B %Y'),
            'calendar_data': [],
            'active_tab': 'assignments',
            'title': 'Назначения сотрудников',
        })
    
    # Получаем все планы для этого расписания
    day_plans = DayPlan.objects.filter(schedule=user_schedule).select_related('duty_type', 'unit').distinct()
    
    # Строим календарь
    calendar_data = AssignmentService.build_calendar_data(day_plans, year, month, access.user_unit)
    
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
    
    return render(request, 'assignments/calendar.html', {
        'year': year,
        'month': month,
        'now_year': today.year,
        'now_month': today.month,
        'month_name': date(year, month, 1).strftime('%B %Y'),
        'calendar_data': weeks,
        'active_tab': 'assignments',
        'title': 'Назначения сотрудников',
    })


@login_required
def get_available_people(request, plan_id):
    """Получить доступных сотрудников (AJAX)"""
    plan = get_object_or_404(DayPlan, pk=plan_id)
    access = AccessService(request.user)
    
    # Проверка прав на редактирование
    can_edit, error_msg = AssignmentService.can_edit_plan(plan, access.user_unit)
    if not can_edit:
        return JsonResponse({'error': error_msg}, status=403)
    
    # Получаем доступных сотрудников
    available, assigned_ids, unavailable = AssignmentService.get_available_people_for_plan(plan, access.user_unit)
    
    return JsonResponse({
        'plan_id': plan.id,
        'duty_name': plan.duty_type.name,
        'unit_name': plan.unit.name,
        'date': plan.date.strftime('%d.%m.%Y'),
        'required_people': plan.duty_type.required_people,
        'current_count': plan.assignments.count(),
        'available': [{'id': p.id, 'name': p.full_name(), 'rank': p.rank.name} for p in available],
        'assigned': [{'id': a.id, 'name': a.person.full_name(), 'rank': a.person.rank.name} for a in plan.assignments.select_related('person', 'person__rank')],
        'unavailable': unavailable,
    })


@login_required
def assign_person(request, plan_id):
    """Назначить сотрудника"""
    plan = get_object_or_404(DayPlan, pk=plan_id)
    person_id = request.POST.get('person_id')
    next_url = request.GET.get('next', '/assignments/')
    
    if not person_id:
        messages.error(request, 'Сотрудник не выбран')
        return redirect('assignment:calendar')
    
    person = get_object_or_404(Person, pk=person_id)
    access = AccessService(request.user)
    
    # Проверка прав
    can_edit, error_msg = AssignmentService.can_edit_plan(plan, access.user_unit)
    if not can_edit:
        messages.error(request, error_msg)
        return redirect('assignment:calendar')
    
    # Проверка возможности назначения
    can_assign, error_msg = AssignmentService.can_assign_to_plan(plan, access.user_unit, person)
    if not can_assign:
        messages.error(request, error_msg)
        return redirect('assignment:calendar')
    
    # Создаём назначение
    _, created = DutyAssignment.objects.get_or_create(
        day_plan=plan,
        person=person,
        defaults={'assigned_by': request.user}
    )
    
    if created:
        messages.success(request, f'Сотрудник {person.full_name()} назначен')
    else:
        messages.warning(request, f'Сотрудник {person.full_name()} уже назначен')
    
    return redirect(f"{next_url}?year={plan.date.year}&month={plan.date.month}")


@login_required
def unassign_person(request, assignment_id):
    """Снять назначение"""
    assignment = get_object_or_404(DutyAssignment, pk=assignment_id)
    access = AccessService(request.user)
    plan = assignment.day_plan
    next_url = request.GET.get('next', '/assignments/')
    
    # Проверка прав
    can_edit, error_msg = AssignmentService.can_edit_plan(plan, access.user_unit)
    if not can_edit:
        messages.error(request, error_msg)
        return redirect('assignment:calendar')
    
    person_name = assignment.person.full_name()
    assignment.delete()
    messages.success(request, f'Назначение сотрудника {person_name} снято')
    
    return redirect(f"{next_url}?year={plan.date.year}&month={plan.date.month}")