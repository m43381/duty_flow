from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from datetime import datetime
import calendar

from core.crud import crud_views
from duty_plans.models import MonthlySchedule, DayPlan
from duty_plans.forms import MonthlyScheduleForm, DayPlanForm
from duty_types.models import DutyType
from users_app.access_service import AccessService


# ========== БАЗОВЫЙ CRUD ДЛЯ РАСПИСАНИЙ (только delete) ==========

schedule_views = crud_views(
    model=MonthlySchedule,
    form_class=MonthlyScheduleForm,
    template_prefix='schedule',
    list_url_name='plan:list',
    extra_context={'active_tab': 'plans'},
)

# Используем только delete из CRUD
schedule_delete = schedule_views['delete']


# ========== СПИСОК РАСПИСАНИЙ ==========

@login_required
def schedule_list(request):
    """Список всех расписаний"""
    schedules = MonthlySchedule.objects.all().order_by('-month')
    
    context = {
        'items': schedules,
        'active_tab': 'plans',
        'title': 'Расписания нарядов',
        'can_add': True,
    }
    return render(request, 'schedule/list.html', context)


# ========== СОЗДАНИЕ РАСПИСАНИЯ ==========

@login_required
def schedule_add(request):
    """Создание расписания"""
    if request.method == 'POST':
        form = MonthlyScheduleForm(request.POST, user=request.user)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            messages.success(request, f'Расписание "{schedule}" создано')
            return redirect('plan:days', pk=schedule.pk)
    else:
        form = MonthlyScheduleForm(user=request.user)
    
    context = {
        'form': form,
        'active_tab': 'plans',
        'title': 'Создание расписания',
    }
    return render(request, 'schedule/form.html', context)


# ========== РЕДАКТИРОВАНИЕ РАСПИСАНИЯ (общие поля) ==========

@login_required
def schedule_edit(request, pk):
    """Редактирование расписания (общие поля)"""
    schedule = get_object_or_404(MonthlySchedule, pk=pk)
    
    if request.method == 'POST':
        form = MonthlyScheduleForm(request.POST, instance=schedule, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Расписание обновлено')
            return redirect('plan:detail', pk=schedule.pk)
    else:
        form = MonthlyScheduleForm(instance=schedule, user=request.user)
    
    context = {
        'form': form,
        'item': schedule,
        'active_tab': 'plans',
        'title': 'Редактирование расписания',
    }
    return render(request, 'schedule/form.html', context)


# ========== ПРОСМОТР РАСПИСАНИЯ ==========

@login_required
def schedule_detail(request, pk):
    """Просмотр расписания"""
    schedule = get_object_or_404(MonthlySchedule, pk=pk)
    
    context = {
        'item': schedule,
        'active_tab': 'plans',
        'title': f'Расписание: {schedule}',
        'can_edit': True,
    }
    return render(request, 'schedule/detail.html', context)


# ========== УДАЛЕНИЕ РАСПИСАНИЯ ==========

# schedule_delete уже есть из CRUD


# ========== РЕДАКТИРОВАНИЕ ДНЕЙ (ТАБЛИЦА) ==========

@login_required
def schedule_days(request, pk):
    """Редактирование дней в расписании"""
    schedule = get_object_or_404(MonthlySchedule, pk=pk)
    access = AccessService(request.user)
    
    # Получаем все дни месяца
    year = schedule.month.year
    month = schedule.month.month
    last_day = calendar.monthrange(year, month)[1]
    dates = [datetime(year, month, day).date() for day in range(1, last_day + 1)]
    
    # Доступные типы нарядов
    available_duty_types = DutyType.objects.all()
    
    # Доступные подразделения для выбора
    available_units = access.get_visible_units()
    
    # Строим матрицу существующих планов
    plan_matrix = {}
    for dp in schedule.days.all():
        key = f"{dp.date}_{dp.duty_type_id}"
        plan_matrix[key] = dp.unit_id
    
    if request.method == 'POST':
        with transaction.atomic():
            created_count = 0
            updated_count = 0
            kept_keys = []
            
            for key, value in request.POST.items():
                if key.startswith('day_') and value:
                    parts = key.split('_')
                    if len(parts) == 3:
                        date_str = parts[1]
                        duty_type_id = int(parts[2])
                        unit_id = int(value)
                        
                        try:
                            date = datetime.strptime(date_str, '%Y-%m-%d').date()
                            kept_keys.append((date, duty_type_id))
                            
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
        'title': f'Редактирование дней: {schedule}',
    }
    return render(request, 'schedule/days.html', context)