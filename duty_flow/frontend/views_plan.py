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


@login_required
def list(request):
    schedules = MonthlySchedule.objects.filter(unit=request.user.profile.unit).order_by('-month')
    return render(request, 'plan/list.html', {'schedules': schedules, 'active_tab': 'plans'})


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
    if schedule.unit != request.user.profile.unit:
        messages.error(request, 'Нет прав')
        return redirect('plan:list')
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Удалено')
        return redirect('plan:list')
    return render(request, 'plan/delete.html', {'schedule': schedule, 'active_tab': 'plans'})


@login_required
def days(request, pk):
    schedule = get_object_or_404(MonthlySchedule, pk=pk)
    user_unit = request.user.profile.unit
    
    if schedule.unit != user_unit:
        messages.error(request, 'Нет прав')
        return redirect('plan:list')
    
    # Дни месяца
    year = schedule.month.year
    month = schedule.month.month
    last_day = calendar.monthrange(year, month)[1]
    dates = [datetime(year, month, day).date() for day in range(1, last_day + 1)]
    
    # Все типы нарядов, которые есть в назначениях
    all_plans = schedule.days.all()
    
    # Собираем ID типов нарядов из:
    # 1. Своих нарядов (type='own')
    # 2. Принятых входящих (type='incoming', status='accepted')
    duty_ids = set()
    for p in all_plans:
        if p.type == 'own' or (p.type == 'incoming' and p.status == 'accepted'):
            duty_ids.add(p.duty_type_id)
    
    # Добавляем типы, созданные этим подразделением (для пустых ячеек)
    own_duty_types = DutyType.objects.filter(created_by_unit=user_unit)
    for dt in own_duty_types:
        duty_ids.add(dt.id)
    
    duty_types = DutyType.objects.filter(id__in=duty_ids).order_by('name')
    
    # Словарь существующих назначений
    existing = {}
    for p in all_plans:
        if p.type == 'own' or (p.type == 'incoming' and p.status == 'accepted'):
            existing[(p.date, p.duty_type_id)] = p
    
    # День входящего назначения для каждого типа наряда
    incoming_day = {}
    for p in all_plans:
        if p.type == 'incoming' and p.status == 'accepted':
            incoming_day[p.duty_type_id] = p.date
    
    children = user_unit.children.all()
    
    if request.method == 'POST':
        with transaction.atomic():
            # Удаляем все старые назначения
            schedule.days.all().delete()
            
            for key, value in request.POST.items():
                if key.startswith('day_') and value:
                    parts = key.split('_')
                    if len(parts) == 3:
                        date_str = parts[1]
                        duty_id = int(parts[2])
                        date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        unit_id = int(value)
                        
                        if unit_id == user_unit.id:
                            DayPlan.objects.create(
                                schedule=schedule,
                                date=date,
                                duty_type_id=duty_id,
                                unit_id=unit_id,
                                type='own',
                                status=None,
                                child_status='none'
                            )
                        else:
                            parent_plan, created = DayPlan.objects.get_or_create(
                                schedule=schedule,
                                date=date,
                                duty_type_id=duty_id,
                                defaults={
                                    'unit_id': unit_id,
                                    'type': 'own',
                                    'status': None,
                                    'child_status': 'pending'
                                }
                            )
                            if not created:
                                parent_plan.unit_id = unit_id
                                parent_plan.child_status = 'pending'
                                parent_plan.save()
                            
                            child_schedule, _ = MonthlySchedule.objects.get_or_create(
                                month=schedule.month,
                                unit_id=unit_id,
                                defaults={
                                    'name': f"Расписание {schedule.month.strftime('%B %Y')}",
                                    'status': 'draft',
                                    'parent_schedule': schedule,
                                    'created_by': request.user
                                }
                            )
                            
                            DayPlan.objects.update_or_create(
                                schedule=child_schedule,
                                date=date,
                                duty_type_id=duty_id,
                                defaults={
                                    'unit_id': unit_id,
                                    'type': 'incoming',
                                    'status': 'pending',
                                    'child_status': 'none',
                                    'parent': parent_plan
                                }
                            )
            
            messages.success(request, 'Сохранено')
            return redirect('plan:days', pk=schedule.pk)
    
    # Строим таблицу
    table = []
    for duty in duty_types:
        row = {'duty': duty, 'cells': []}
        inc_date = incoming_day.get(duty.id)
        
        for date in dates:
            p = existing.get((date, duty.id))
            is_incoming_day = (inc_date == date)
            
            # Определяем, можно ли редактировать
            if p:
                if p.type == 'own':
                    can_edit = True
                elif p.type == 'incoming' and p.status == 'accepted':
                    can_edit = True
                else:
                    can_edit = False
            else:
                # Пустая ячейка — активна только если это свой наряд или день входящего
                can_edit = (duty.created_by_unit_id == user_unit.id) or is_incoming_day
            
            row['cells'].append({
                'date': date,
                'unit_id': p.unit_id if p else None,
                'unit_name': p.unit.name if p and p.unit else None,
                'can_edit': can_edit,
                'is_incoming_day': is_incoming_day
            })
        table.append(row)
    
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
    source = get_object_or_404(DayPlan, pk=plan_id)
    user_unit = request.user.profile.unit
    
    if source.unit != user_unit or source.type != 'incoming' or source.status != 'pending':
        messages.error(request, 'Не может быть принято')
        return redirect('plan:incoming')
    
    with transaction.atomic():
        schedule, _ = MonthlySchedule.objects.get_or_create(
            month=source.schedule.month,
            unit=user_unit,
            defaults={
                'name': f"Расписание {source.schedule.month.strftime('%B %Y')}",
                'status': 'draft',
                'parent_schedule': source.schedule,
                'created_by': request.user
            }
        )
        
        DayPlan.objects.update_or_create(
            schedule=schedule,
            date=source.date,
            duty_type=source.duty_type,
            defaults={
                'unit': user_unit,
                'type': 'incoming',
                'status': 'accepted',
                'child_status': 'none',
                'parent': source
            }
        )
        
        source.status = 'accepted'
        source.save()
        
        if source.parent:
            source.parent.child_status = 'accepted'
            source.parent.save()
    
    messages.success(request, f'Назначение на {source.date} принято')
    return redirect('plan:days', pk=schedule.pk)