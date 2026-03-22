from core.crud import crud_views
from duty_plans.models import MonthlySchedule
from duty_plans.forms import MonthlyScheduleForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from datetime import datetime
import calendar
from duty_plans.models import DayPlan

from users_app.access_service import AccessService


# ========== БАЗОВЫЙ CRUD (без unit) ==========

plan_views = crud_views(
    model=MonthlySchedule,
    form_class=MonthlyScheduleForm,
    template_prefix='plan',
    list_url_name='plan:list',
    has_unit_field=False,  # У MonthlySchedule нет поля unit
    extra_context={'active_tab': 'plans'},
)

plan_list = plan_views['list']
plan_add = plan_views['create']
plan_edit = plan_views['update']
plan_delete = plan_views['delete']
plan_detail = plan_views['detail']


# ========== РЕДАКТИРОВАНИЕ ДНЕЙ (ТАБЛИЦА) ==========

@login_required
def plan_days(request, pk):
    plan = get_object_or_404(MonthlySchedule, pk=pk)
    access = AccessService(request.user)
    
    year = plan.month.year
    month = plan.month.month
    last_day = calendar.monthrange(year, month)[1]
    dates = [datetime(year, month, day).date() for day in range(1, last_day + 1)]
    
    from duty_types.models import DutyType
    duty_types = DutyType.objects.all()
    available_units = access.get_visible_units()
    
    # Получаем все назначения
    assignments = plan.days.all()
    
    # Строим матрицу: (date, duty_type_id) -> unit_id
    matrix = {}
    for a in assignments:
        matrix[(a.date, a.duty_type_id)] = a.unit_id
    
    if request.method == 'POST':
        with transaction.atomic():
            # Собираем все ключи из POST (включая пустые)
            post_data = {}
            for key, value in request.POST.items():
                if key.startswith('day_'):
                    # Сохраняем даже пустые значения
                    post_data[key] = value if value else None
            
            print(f"POST данные: {post_data}")
            
            for key, unit_id in post_data.items():
                parts = key.split('_')
                if len(parts) == 3:
                    date_str = parts[1]
                    duty_type_id = int(parts[2])
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    if unit_id is not None:
                        # Есть значение — создаем или обновляем
                        DayPlan.objects.update_or_create(
                            schedule=plan,
                            date=date,
                            duty_type_id=duty_type_id,
                            defaults={'unit_id': unit_id}
                        )
                        print(f"Создано/обновлено: {date}, тип={duty_type_id}, подр={unit_id}")
                    else:
                        # Пустое значение — удаляем
                        DayPlan.objects.filter(
                            schedule=plan,
                            date=date,
                            duty_type_id=duty_type_id
                        ).delete()
                        print(f"Удалено: {date}, тип={duty_type_id}")
            
            messages.success(request, 'Сохранено')
            return redirect('plan:days', pk=plan.pk)
    
    # Подготавливаем данные для таблицы
    table_data = []
    for duty_type in duty_types:
        row = {
            'duty_type': duty_type,
            'cells': []
        }
        for date in dates:
            unit_id = matrix.get((date, duty_type.id))
            row['cells'].append({
                'date': date,
                'unit_id': unit_id,
                'unit_name': next((u.name for u in available_units if u.id == unit_id), None) if unit_id else None
            })
        table_data.append(row)
    
    context = {
        'plan': plan,
        'dates': dates,
        'duty_types': duty_types,
        'table_data': table_data,
        'available_units': available_units,
        'active_tab': 'plans',
        'title': f'Редактирование: {plan}',
    }
    return render(request, 'plan/days.html', context)