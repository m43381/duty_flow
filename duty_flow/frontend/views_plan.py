from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from datetime import datetime, timedelta
import calendar

from core.crud import crud_views
from duty_plans.models import MonthlySchedule, DayPlan
from duty_plans.forms import MonthlyScheduleForm, DayPlanForm
from duty_types.models import DutyType
from users_app.access_service import AccessService


# ========== БАЗОВЫЙ CRUD ДЛЯ РАСПИСАНИЙ ==========

schedule_views = crud_views(
    model=MonthlySchedule,
    form_class=MonthlyScheduleForm,
    template_prefix='schedule',
    list_url_name='plan:list',
    extra_context={'active_tab': 'plans'},
)

schedule_list = schedule_views['list']
schedule_add = schedule_views['create']
schedule_edit = schedule_views['update']
schedule_delete = schedule_views['delete']


# ========== КАСТОМНЫЙ DETAIL ДЛЯ РАСПИСАНИЙ ==========

@login_required
def schedule_detail(request, pk):
    """Просмотр расписания (информация о расписании)"""
    schedule = get_object_or_404(MonthlySchedule, pk=pk)
    access = AccessService(request.user)
    
    if not access.can_view_schedule(schedule):
        messages.error(request, 'Нет доступа к этому расписанию')
        return redirect('plan:list')
    
    context = {
        'item': schedule,
        'active_tab': 'plans',
        'title': f'Расписание: {schedule}',
        'can_edit': access.can_edit_schedule(schedule),
    }
    return render(request, 'schedule/detail.html', context)


# ========== РЕДАКТИРОВАНИЕ ДНЕЙ (ТАБЛИЦА) ==========

@login_required
def schedule_days(request, pk):
    """
    Редактирование дней в расписании.
    Таблица: типы нарядов (строки) × даты (столбцы) → подразделения (ячейки)
    """
    schedule = get_object_or_404(MonthlySchedule, pk=pk)
    access = AccessService(request.user)
    
    if not access.can_edit_schedule(schedule):
        messages.error(request, 'Нет прав для редактирования')
        return redirect('plan:detail', pk=pk)
    
    # Получаем все дни месяца
    year = schedule.month.year
    month = schedule.month.month
    last_day = calendar.monthrange(year, month)[1]
    dates = [datetime(year, month, day).date() for day in range(1, last_day + 1)]
    
    # Доступные типы нарядов
    available_duty_types = DutyType.objects.all()
    
    # Доступные подразделения для выбора
    available_units = access.get_visible_units()
    
    # Получаем существующие планы на день для этого расписания
    day_plans = {dp.date: dp for dp in schedule.days.all()}
    
    # Строим матрицу для быстрого доступа
    plan_matrix = {}
    for dp in schedule.days.all():
        key = f"{dp.date}_{dp.duty_type_id}"
        plan_matrix[key] = dp.unit_id
    
    # Обработка POST (сохранение)
    if request.method == 'POST':
        with transaction.atomic():
            created_count = 0
            updated_count = 0
            deleted_count = 0
            
            # Сохраняем ключи существующих планов
            kept_keys = []
            
            # Обрабатываем POST данные
            for key, value in request.POST.items():
                if key.startswith('day_') and value:
                    # Формат: day_2026-03-15_5 (дата_id_типа)
                    parts = key.split('_')
                    if len(parts) == 3:
                        date_str = parts[1]
                        duty_type_id = int(parts[2])
                        unit_id = int(value)
                        
                        try:
                            date = datetime.strptime(date_str, '%Y-%m-%d').date()
                            kept_keys.append((date, duty_type_id))
                            
                            # Создаем или обновляем
                            day_plan, created = DayPlan.objects.update_or_create(
                                schedule=schedule,
                                date=date,
                                duty_type_id=duty_type_id,
                                defaults={'unit_id': unit_id}
                            )
                            
                            if created:
                                created_count += 1
                            else:
                                updated_count += 1
                                
                        except (ValueError, TypeError):
                            continue
            
            # Удаляем планы, которые были очищены
            deleted_count = schedule.days.exclude(
                date__in=[k[0] for k in kept_keys],
                duty_type_id__in=[k[1] for k in kept_keys]
            ).delete()[0]
            
            messages.success(
                request,
                f'Сохранено: создано {created_count}, обновлено {updated_count}, удалено {deleted_count}'
            )
            return redirect('plan:days', pk=schedule.pk)
    
    context = {
        'schedule': schedule,
        'dates': dates,
        'available_duty_types': available_duty_types,
        'available_units': available_units,
        'plan_matrix': plan_matrix,
        'active_tab': 'plans',
        'title': f'Редактирование: {schedule}',
    }
    return render(request, 'schedule/days.html', context)