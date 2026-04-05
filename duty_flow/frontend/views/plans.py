from datetime import datetime
import calendar
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction

from duty_plans.models import MonthlySchedule, DayPlan
from duty_plans.forms import MonthlyScheduleForm
from duty_types.models import DutyType
from users_app.access_service import AccessService
from frontend.services.plan_service import PlanService

import logging
logger = logging.getLogger(__name__)


@login_required
def list(request):
    schedules = MonthlySchedule.objects.filter(unit=request.user.profile.unit).order_by('-month')
    return render(request, 'plan/list.html', {
        'schedules': schedules, 
        'active_tab': 'plans',
        'title': 'Мои типы нарядов',
    })


@login_required
def add(request):
    if request.method == 'POST':
        form = MonthlyScheduleForm(request.POST, user=request.user)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.unit = request.user.profile.unit
            schedule.save()
            messages.success(request, 'Расписание создано')
            return redirect('plan:days', pk=schedule.pk)
    else:
        form = MonthlyScheduleForm(user=request.user)
    return render(request, 'plan/form.html', {'form': form, 'active_tab': 'plans'})


@login_required
def detail(request, pk):
    schedule = get_object_or_404(MonthlySchedule, pk=pk)
    return render(request, 'plan/detail.html', {'schedule': schedule, 'active_tab': 'plans'})


@login_required
def edit(request, pk):
    schedule = get_object_or_404(MonthlySchedule, pk=pk)
    if schedule.unit != request.user.profile.unit:
        messages.error(request, 'Нет прав')
        return redirect('plan:list')
    if request.method == 'POST':
        form = MonthlyScheduleForm(request.POST, instance=schedule, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Обновлено')
            return redirect('plan:detail', pk=schedule.pk)
    else:
        form = MonthlyScheduleForm(instance=schedule, user=request.user)
    return render(request, 'plan/form.html', {'form': form, 'schedule': schedule, 'active_tab': 'plans'})


@login_required
def delete(request, pk):
    schedule = get_object_or_404(MonthlySchedule, pk=pk)
    access = AccessService(request.user)
    
    if schedule.unit != access.user_unit:
        messages.error(request, 'Нет прав для удаления')
        return redirect('plan:list')
    
    if request.method == 'POST':
        PlanService.delete_schedule_with_children(schedule)
        messages.success(request, 'Расписание и все связанные данные удалены')
        return redirect('plan:list')
    
    return render(request, 'plan/delete.html', {
        'schedule': schedule,
        'active_tab': 'plans',
        'title': 'Удаление расписания'
    })


@login_required
def days(request, pk):
    schedule = get_object_or_404(MonthlySchedule, pk=pk)
    user_unit = request.user.profile.unit
    
    logger.info("\n" + "=" * 70)
    logger.info("=== DAYS() START ===")
    logger.info(f"Расписание: id={schedule.id}, month={schedule.month}, unit={schedule.unit.name}")
    logger.info(f"Пользователь: {request.user.username}, подразделение: {user_unit.name}")
    
    if schedule.unit != user_unit:
        logger.warning(f"Нет прав: расписание принадлежит {schedule.unit.name}")
        messages.error(request, 'Нет прав')
        return redirect('plan:list')
    
    # Получаем данные для таблицы через сервис
    dates, duty_types, plans_dict, incoming_day, children = PlanService.build_table_data(schedule, user_unit)
    
    if request.method == 'POST':
        logger.info("\n--- ОБРАБОТКА POST ЗАПРОСА ---")
        PlanService.process_post_data(schedule, request.POST, plans_dict, incoming_day, user_unit, request.user)
        messages.success(request, 'Сохранено')
        return redirect('plan:days', pk=schedule.pk)
    
    # Строим таблицу через сервис
    table = PlanService.build_table_rows(dates, duty_types, plans_dict, incoming_day, user_unit)
    
    logger.info(f"\n--- ИТОГО СТРОК В ТАБЛИЦЕ: {len(table)} ---")
    logger.info("=" * 70 + "\n")
    
    return render(request, 'plan/days.html', {
        'schedule': schedule,
        'dates': dates,
        'table': table,
        'children': children,
        'user_unit': user_unit,
        'active_tab': 'plans'
    })


@login_required
def incoming(request):
    user_unit = request.user.profile.unit
    incoming_plans = DayPlan.objects.filter(
        unit=user_unit, type='incoming', status='pending'
    ).select_related('duty_type', 'parent', 'parent__schedule')
    
    grouped = {}
    for p in incoming_plans:
        src = p.parent.schedule if p.parent else None
        if src not in grouped:
            grouped[src] = []
        grouped[src].append(p)
    
    return render(request, 'plan/incoming.html', {'incoming': grouped, 'active_tab': 'incoming'})


@login_required
def accept(request, plan_id):
    source_plan = get_object_or_404(DayPlan, pk=plan_id)
    user_unit = request.user.profile.unit
    
    logger.info(f"\n=== ACCEPT ===")
    logger.info(f"source: id={source_plan.id}, date={source_plan.date}, duty={source_plan.duty_type.name}")
    logger.info(f"source.unit={source_plan.unit.name if source_plan.unit else 'None'}, type={source_plan.type}, status={source_plan.status}")
    
    if source_plan.unit != user_unit or source_plan.type != 'incoming' or source_plan.status != 'pending':
        logger.warning(f"Не может быть принято")
        messages.error(request, 'Это назначение не может быть принято')
        return redirect('plan:incoming')
    
    schedule = PlanService.accept_incoming_plan(source_plan, request.user)
    
    messages.success(request, f'Назначение на {source_plan.date} принято')
    return redirect('plan:days', pk=schedule.pk)