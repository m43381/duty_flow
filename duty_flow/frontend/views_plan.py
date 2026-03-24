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
        with transaction.atomic():
            # Рекурсивная функция для удаления расписания и всех его потомков
            def delete_schedule_with_children(sched):
                # Находим все дочерние расписания
                children = MonthlySchedule.objects.filter(parent_schedule=sched)
                
                # Рекурсивно удаляем дочерние
                for child in children:
                    delete_schedule_with_children(child)
                
                # Удаляем все DayPlan текущего расписания
                sched.days.all().delete()
                
                # Удаляем само расписание
                sched.delete()
            
            # Запускаем рекурсивное удаление
            delete_schedule_with_children(schedule)
        
        messages.success(request, 'Расписание и все связанные данные удалены')
        return redirect('plan:list')
    
    return render(request, 'plan/delete.html', {
        'schedule': schedule,
        'active_tab': 'plans',
        'title': 'Удаление расписания'
    })


import logging
logger = logging.getLogger(__name__)

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
    
    # Дни месяца
    year = schedule.month.year
    month = schedule.month.month
    last_day = calendar.monthrange(year, month)[1]
    dates = [datetime(year, month, day).date() for day in range(1, last_day + 1)]
    logger.info(f"Дни месяца: {[d.strftime('%Y-%m-%d') for d in dates]}")
    
    # Получаем все назначения
    all_plans = schedule.days.all()
    logger.info(f"\n--- ВСЕ НАЗНАЧЕНИЯ В РАСПИСАНИИ ({all_plans.count()}) ---")
    for p in all_plans:
        logger.info(f"  id={p.id}: date={p.date}, duty={p.duty_type.name}, unit={p.unit.name if p.unit else 'None'}, type={p.type}, status={p.status}, child_status={p.child_status}")
    
    # Собираем ID типов нарядов для отображения
    duty_ids = set()
    for p in all_plans:
        if p.type == 'own' or (p.type == 'incoming' and p.status == 'accepted'):
            duty_ids.add(p.duty_type_id)
            logger.info(f"  Добавлен duty_id={p.duty_type_id} ({p.duty_type.name}) - type={p.type}, status={p.status}")
    
    own_duty_types = DutyType.objects.filter(created_by_unit=user_unit)
    logger.info(f"\n--- СВОИ ТИПЫ НАРЯДОВ (created_by_unit={user_unit.name}) ---")
    for dt in own_duty_types:
        duty_ids.add(dt.id)
        logger.info(f"  id={dt.id}, name={dt.name}")
    
    duty_types = DutyType.objects.filter(id__in=duty_ids).order_by('name')
    logger.info(f"\n--- ИТОГОВЫЕ ТИПЫ ДЛЯ ОТОБРАЖЕНИЯ ({duty_types.count()}) ---")
    for dt in duty_types:
        logger.info(f"  id={dt.id}, name={dt.name}")
    
    # Словарь для быстрого доступа
    plans_dict = {}
    for p in all_plans:
        if p.type == 'own' or (p.type == 'incoming' and p.status == 'accepted'):
            plans_dict[(p.date, p.duty_type_id)] = p
    
    # День входящего назначения
    incoming_day = {}
    for p in all_plans:
        if p.type == 'incoming' and p.status == 'accepted':
            incoming_day[p.duty_type_id] = p.date
            logger.info(f"\n  Входящий наряд: duty_id={p.duty_type_id} ({p.duty_type.name}), date={p.date}, child_status={p.child_status}")
    
    children = user_unit.children.all()
    logger.info(f"\n--- ДОЧЕРНИЕ ПОДРАЗДЕЛЕНИЯ ---")
    for c in children:
        logger.info(f"  id={c.id}, name={c.name}")
    
    if request.method == 'POST':
        logger.info("\n--- ОБРАБОТКА POST ЗАПРОСА ---")
        post_data = {}
        for key, value in request.POST.items():
            if key.startswith('day_') and value:
                parts = key.split('_')
                if len(parts) == 3:
                    date_str = parts[1]
                    duty_id = int(parts[2])
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    unit_id = int(value)
                    post_data[(date, duty_id)] = unit_id
                    logger.info(f"  POST: date={date}, duty_id={duty_id}, unit_id={unit_id}")
        
        with transaction.atomic():
            for (date, duty_id), unit_id in post_data.items():
                existing = plans_dict.get((date, duty_id))
                is_incoming = duty_id in incoming_day
                logger.info(f"\n  Обработка: date={date}, duty_id={duty_id}, unit_id={unit_id}, existing={existing is not None}, is_incoming={is_incoming}")
                
                if unit_id == user_unit.id:
                    # Оставили себе
                    logger.info(f"    -> Оставили себе")
                    if existing:
                        if is_incoming:
                            logger.info(f"       Это входящий наряд, сохраняем как incoming/accepted")
                            existing.type = 'incoming'
                            existing.status = 'accepted'
                            existing.child_status = 'none'
                        else:
                            logger.info(f"       Свой наряд, сохраняем как own")
                            existing.type = 'own'
                            existing.status = None
                            existing.child_status = 'none'
                        existing.unit_id = unit_id
                        existing.save()
                        # Удаляем всех потомков
                        def delete_children(plan):
                            for child in plan.children.all():
                                delete_children(child)
                                logger.info(f"         Удалена дочерняя запись id={child.id}")
                                child.delete()
                        delete_children(existing)
                    else:
                        if is_incoming:
                            logger.info(f"       Создаем новый incoming/accepted")
                            DayPlan.objects.create(
                                schedule=schedule,
                                date=date,
                                duty_type_id=duty_id,
                                unit_id=unit_id,
                                type='incoming',
                                status='accepted',
                                child_status='none'
                            )
                        else:
                            logger.info(f"       Создаем новый own")
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
                    # Делегируем дальше
                    logger.info(f"    -> Делегируем подразделению id={unit_id}")
                    if existing:
                        if is_incoming:
                            logger.info(f"       Входящий наряд, сохраняем как incoming/accepted/pending")
                            existing.type = 'incoming'
                            existing.status = 'accepted'
                            existing.child_status = 'pending'
                        else:
                            logger.info(f"       Свой наряд, сохраняем как own/pending")
                            existing.type = 'own'
                            existing.status = None
                            existing.child_status = 'pending'
                        existing.unit_id = unit_id
                        existing.save()
                    else:
                        if is_incoming:
                            logger.info(f"       Создаем новый incoming/accepted/pending")
                            existing = DayPlan.objects.create(
                                schedule=schedule,
                                date=date,
                                duty_type_id=duty_id,
                                unit_id=unit_id,
                                type='incoming',
                                status='accepted',
                                child_status='pending'
                            )
                        else:
                            logger.info(f"       Создаем новый own/pending")
                            existing = DayPlan.objects.create(
                                schedule=schedule,
                                date=date,
                                duty_type_id=duty_id,
                                unit_id=unit_id,
                                type='own',
                                status=None,
                                child_status='pending'
                            )
                    
                    # Создаем дочернюю запись
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
                    logger.info(f"       child_schedule: id={child_schedule.id}")
                    
                    child_plan = existing.children.first()
                    if child_plan:
                        logger.info(f"       Обновляем существующую дочернюю запись id={child_plan.id}")
                        child_plan.schedule = child_schedule
                        child_plan.unit_id = unit_id
                        child_plan.type = 'incoming'
                        child_plan.status = 'pending'
                        child_plan.child_status = 'none'
                        child_plan.parent = existing
                        child_plan.save()
                    else:
                        logger.info(f"       Создаем новую дочернюю запись")
                        DayPlan.objects.create(
                            schedule=child_schedule,
                            date=date,
                            duty_type_id=duty_id,
                            unit_id=unit_id,
                            type='incoming',
                            status='pending',
                            child_status='none',
                            parent=existing
                        )
            
            # Удаляем записи, которых нет в POST (рекурсивно)
            keys_to_delete = []
            for key in plans_dict.keys():
                if key not in post_data:
                    keys_to_delete.append(key)
            
            logger.info(f"\n--- УДАЛЕНИЕ ЗАПИСЕЙ ({len(keys_to_delete)}) ---")
            
            def delete_with_children(plan, depth=0):
                indent = "  " * depth
                logger.info(f"{indent}Удаляем запись id={plan.id}: date={plan.date}, duty={plan.duty_type.name}")
                for child in plan.children.all():
                    delete_with_children(child, depth + 1)
                logger.info(f"{indent}  Удалена")
                plan.delete()
            
            for key in keys_to_delete:
                p = plans_dict.get(key)
                if p:
                    logger.info(f"\n  Ключ: date={key[0]}, duty_id={key[1]}")
                    delete_with_children(p)
            
            messages.success(request, 'Сохранено')
            return redirect('plan:days', pk=schedule.pk)
    
    # Строим таблицу
    logger.info("\n--- ПОСТРОЕНИЕ ТАБЛИЦЫ ---")
    table = []
    for duty in duty_types:
        row = {'duty': duty, 'cells': []}
        inc_date = incoming_day.get(duty.id)
        logger.info(f"\nТип наряда: {duty.name}, inc_date={inc_date}")
        
        for date in dates:
            p = plans_dict.get((date, duty.id))
            is_incoming_day = (inc_date == date)
            
            if p:
                if p.type == 'own':
                    if p.child_status == 'none':
                        cell_class = 'own'
                        status_text = 'Своими силами'
                    elif p.child_status == 'pending':
                        cell_class = 'delegated_pending'
                        status_text = 'Делегировано, ждет'
                    else:
                        cell_class = 'delegated_accepted'
                        status_text = 'Делегировано, принято'
                    can_edit = True
                    logger.info(f"  {date}: СВОЙ наряд, child_status={p.child_status}, класс={cell_class}")
                else:  # type == 'incoming'
                    if p.status == 'accepted':
                        if p.child_status == 'pending':
                            cell_class = 'incoming_delegated_pending'
                            status_text = 'Получен, делегирован, ждет'
                        elif p.child_status == 'accepted':
                            cell_class = 'incoming_delegated_accepted'
                            status_text = 'Получен, делегирован, принят'
                        else:
                            cell_class = 'incoming_active'
                            status_text = 'Принят, исполняем'
                        can_edit = True
                        logger.info(f"  {date}: ВХОДЯЩИЙ ПРИНЯТЫЙ, child_status={p.child_status}, класс={cell_class}")
                    else:
                        cell_class = 'incoming_pending'
                        status_text = 'Ожидает принятия'
                        can_edit = False
                        logger.info(f"  {date}: ВХОДЯЩИЙ НЕ ПРИНЯТ, status={p.status}")
            else:
                if duty.created_by_unit_id == user_unit.id:
                    can_edit = True
                    cell_class = 'empty'
                    status_text = ''
                    logger.info(f"  {date}: ПУСТАЯ (свой тип), можно редактировать")
                elif is_incoming_day:
                    can_edit = True
                    cell_class = 'incoming_active'
                    status_text = 'Входящий'
                    logger.info(f"  {date}: ПУСТАЯ (входящий день), можно редактировать")
                else:
                    can_edit = False
                    cell_class = 'inactive'
                    status_text = ''
                    logger.info(f"  {date}: ПУСТАЯ (неактивна)")
            
            row['cells'].append({
                'date': date,
                'unit_id': p.unit_id if p else None,
                'unit_name': p.unit.name if p and p.unit else None,
                'cell_class': cell_class,
                'status_text': status_text,
                'can_edit': can_edit
            })
        table.append(row)
    
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
    source = get_object_or_404(DayPlan, pk=plan_id)
    user_unit = request.user.profile.unit
    
    logger.info(f"\n=== ACCEPT ===")
    logger.info(f"source: id={source.id}, date={source.date}, duty={source.duty_type.name}")
    logger.info(f"source.unit={source.unit.name if source.unit else 'None'}, type={source.type}, status={source.status}")
    
    if source.unit != user_unit or source.type != 'incoming' or source.status != 'pending':
        logger.warning(f"Не может быть принято")
        messages.error(request, 'Это назначение не может быть принято')
        return redirect('plan:incoming')
    
    with transaction.atomic():
        # Получаем или создаем расписание для этого подразделения
        schedule, created = MonthlySchedule.objects.get_or_create(
            month=source.schedule.month,
            unit=user_unit,
            defaults={
                'name': f"Расписание {source.schedule.month.strftime('%B %Y')}",
                'status': 'draft',
                'parent_schedule': source.schedule,
                'created_by': request.user
            }
        )
        logger.info(f"Расписание: {'создано' if created else 'найдено'} id={schedule.id}")
        
        # Создаем принятую запись в своем расписании (ВАЖНО: type='incoming', status='accepted')
        day_plan, created = DayPlan.objects.get_or_create(
            schedule=schedule,
            date=source.date,
            duty_type=source.duty_type,
            defaults={
                'unit': user_unit,
                'type': 'incoming',      # ДОЛЖНО БЫТЬ incoming!
                'status': 'accepted',    # ДОЛЖНО БЫТЬ accepted!
                'child_status': 'none',
                'parent': source
            }
        )
        logger.info(f"Создана запись: id={day_plan.id}, type={day_plan.type}, status={day_plan.status}")
        
        # Обновляем исходное назначение (оно в расписании родителя)
        source.status = 'accepted'
        source.save()
        logger.info(f"Исходное назначение обновлено: status={source.status}")
        
        # Обновляем родительскую запись (если есть)
        if source.parent:
            source.parent.child_status = 'accepted'
            source.parent.save()
            logger.info(f"Родительская запись обновлена: id={source.parent.id}, child_status={source.parent.child_status}")
    
    messages.success(request, f'Назначение на {source.date} принято')
    return redirect('plan:days', pk=schedule.pk)