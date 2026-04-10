from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now

from access_control.services import AccessManager
from duty_plans.models import MonthlySchedule, DayPlan
from duty_plans.forms import MonthlyScheduleForm
from core.services.plan_service import PlanService

import logging

logger = logging.getLogger(__name__)


def apply_plan_access_to_form(form, access_manager, action: str):
    visible_fields = set(access_manager.visible_plan_fields(action))
    editable_fields = set(access_manager.editable_plan_fields(action))

    for field_name in list(form.fields.keys()):
        if field_name not in visible_fields:
            form.fields.pop(field_name, None)
            continue

        if field_name not in editable_fields:
            form.fields[field_name].disabled = True


@login_required
def list(request):
    access = AccessManager(request.user)

    schedules = access.scope_plans(
        MonthlySchedule.objects.select_related("unit", "parent_schedule", "created_by").order_by("-month")
    )

    search_query = request.GET.get("q", "").strip()
    if search_query:
        schedules = schedules.filter(name__icontains=search_query)

    return render(request, "app/plans/list.html", {
        "schedules": schedules,
        "active_tab": "plans",
        "page_title": "Планы нарядов",
        "page_subtitle": "Месячные расписания, доступные пользователю",
        "search_query": search_query,
        "can_add": access.can_plan("create"),
        "title": "Планы нарядов",
    })


@login_required
def add(request):
    access = AccessManager(request.user)

    if not access.can_plan("create"):
        messages.error(request, "Нет прав на создание")
        return redirect("plan:list")

    if request.method == "POST":
        form = MonthlyScheduleForm(request.POST, user=request.user)
        apply_plan_access_to_form(form, access, "create")

        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.unit = request.user.profile.unit

            if not schedule.name:
                schedule.name = f"Расписание {schedule.month.strftime('%B %Y')}"

            schedule.save()
            messages.success(request, "Расписание создано")
            return redirect("plan:detail", pk=schedule.pk)
    else:
        form = MonthlyScheduleForm(
            user=request.user,
            initial={"month": now().date().replace(day=1)}
        )
        apply_plan_access_to_form(form, access, "create")

    return render(request, "app/plans/form.html", {
        "form": form,
        "schedule": None,
        "active_tab": "plans",
        "page_title": "Планы нарядов",
        "page_subtitle": "Создание расписания",
        "title": "Создать расписание",
    })


@login_required
def detail(request, pk):
    access = AccessManager(request.user)
    schedule = get_object_or_404(
        MonthlySchedule.objects.select_related("unit", "parent_schedule", "created_by"),
        pk=pk
    )

    if not access.can_plan("view", schedule):
        messages.error(request, "Нет доступа")
        return redirect("plan:list")

    day_plans_count = schedule.days.count()
    accepted_count = schedule.days.filter(status="accepted").count()
    pending_count = schedule.days.filter(status="pending").count()
    child_schedules_count = MonthlySchedule.objects.filter(parent_schedule=schedule).count()

    return render(request, "app/plans/detail.html", {
        "schedule": schedule,
        "day_plans_count": day_plans_count,
        "accepted_count": accepted_count,
        "pending_count": pending_count,
        "child_schedules_count": child_schedules_count,
        "can_edit": access.can_plan("update", schedule),
        "can_delete": access.can_plan("delete", schedule),
        "can_manage_days": access.can_plan("manage_days", schedule),
        "active_tab": "plans",
        "page_title": "Планы нарядов",
        "page_subtitle": "Карточка расписания",
        "title": schedule.name or str(schedule),
    })


@login_required
def edit(request, pk):
    access = AccessManager(request.user)
    schedule = get_object_or_404(MonthlySchedule, pk=pk)

    if not access.can_plan("update", schedule):
        messages.error(request, "Нет прав")
        return redirect("plan:list")

    if request.method == "POST":
        form = MonthlyScheduleForm(request.POST, instance=schedule, user=request.user)
        apply_plan_access_to_form(form, access, "update")

        if form.is_valid():
            form.save()
            messages.success(request, "Расписание обновлено")
            return redirect("plan:detail", pk=schedule.pk)
    else:
        form = MonthlyScheduleForm(instance=schedule, user=request.user)
        apply_plan_access_to_form(form, access, "update")

    return render(request, "app/plans/form.html", {
        "form": form,
        "schedule": schedule,
        "active_tab": "plans",
        "page_title": "Планы нарядов",
        "page_subtitle": "Редактирование расписания",
        "title": "Редактировать расписание",
    })


@login_required
def delete(request, pk):
    access = AccessManager(request.user)
    schedule = get_object_or_404(MonthlySchedule, pk=pk)

    if not access.can_plan("delete", schedule):
        messages.error(request, "Нет прав для удаления")
        return redirect("plan:list")

    if request.method == "POST":
        schedule_name = schedule.name or str(schedule)
        PlanService.delete_schedule_with_children(schedule)
        messages.success(request, f'Расписание "{schedule_name}" и все связанные данные удалены')
        return redirect("plan:list")

    return render(request, "app/plans/delete.html", {
        "schedule": schedule,
        "day_plans_count": schedule.days.count(),
        "child_schedules_count": MonthlySchedule.objects.filter(parent_schedule=schedule).count(),
        "active_tab": "plans",
        "page_title": "Планы нарядов",
        "page_subtitle": "Удаление расписания",
        "title": "Удаление расписания",
    })


@login_required
def days(request, pk):
    access = AccessManager(request.user)
    schedule = get_object_or_404(MonthlySchedule, pk=pk)
    user_unit = request.user.profile.unit

    logger.info("\n" + "=" * 70)
    logger.info("=== DAYS() START ===")
    logger.info(f"Расписание: id={schedule.id}, month={schedule.month}, unit={schedule.unit.name}")
    logger.info(f"Пользователь: {request.user.username}, подразделение: {user_unit.name}")

    if not access.can_plan("manage_days", schedule):
        logger.warning("Нет прав на управление днями")
        messages.error(request, "Нет прав")
        return redirect("plan:list")

    allowed_delegate_units = access.allowed_delegate_units_for_plan_days(schedule).exclude(id=user_unit.id)

    dates, duty_types, plans_dict, incoming_day = PlanService.build_table_data(schedule, user_unit)
    delegate_units = allowed_delegate_units.all()

    weekday_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    date_headers = []
    for date in dates:
        weekday_index = date.weekday()
        date_headers.append({
            "date": date,
            "day": date.day,
            "weekday_short": weekday_names[weekday_index],
            "is_weekend": weekday_index >= 5,
        })

    if request.method == "POST":
        logger.info("\n--- ОБРАБОТКА POST ЗАПРОСА ---")
        PlanService.process_post_data(
            schedule=schedule,
            post_data=request.POST,
            plans_dict=plans_dict,
            incoming_day=incoming_day,
            user_unit=user_unit,
            user=request.user,
            allowed_delegate_units=allowed_delegate_units,
        )
        messages.success(request, "Сохранено")
        return redirect("plan:days", pk=schedule.pk)

    table = PlanService.build_table_rows(
        dates=dates,
        duty_types=duty_types,
        plans_dict=plans_dict,
        incoming_day=incoming_day,
        user_unit=user_unit,
        allowed_delegate_units=allowed_delegate_units,
    )

    logger.info(f"\n--- ИТОГО СТРОК В ТАБЛИЦЕ: {len(table)} ---")
    logger.info("=" * 70 + "\n")

    return render(request, "app/plans/days.html", {
        "schedule": schedule,
        "dates": dates,
        "date_headers": date_headers,
        "table": table,
        "delegate_units": delegate_units,
        "user_unit": user_unit,
        "active_tab": "plans",
        "page_title": "Планы нарядов",
        "page_subtitle": "Таблица нарядов по дням",
        "title": schedule.name or str(schedule),
        "duty_types_count": len(duty_types),
        "dates_count": len(dates),
        "incoming_day": incoming_day,
    })


@login_required
def incoming(request):
    access = AccessManager(request.user)
    user_unit = request.user.profile.unit

    if not access.can_plan("accept_incoming"):
        messages.error(request, "Нет доступа")
        return redirect("plan:list")

    incoming_plans = (
        DayPlan.objects
        .filter(unit=user_unit, type="incoming", status="pending")
        .select_related("duty_type", "parent", "parent__schedule", "parent__schedule__unit")
        .order_by("date", "duty_type__name")
    )

    grouped = {}
    total_count = 0

    for plan in incoming_plans:
        source_schedule = plan.parent.schedule if plan.parent else None

        if source_schedule not in grouped:
            grouped[source_schedule] = {
                "source_schedule": source_schedule,
                "items": [],
                "count": 0,
            }

        grouped[source_schedule]["items"].append(plan)
        grouped[source_schedule]["count"] += 1
        total_count += 1

    groups = [group for group in grouped.values()]

    return render(request, "app/plans/incoming.html", {
        "groups": groups,
        "total_count": total_count,
        "active_tab": "plans",
        "page_title": "Планы нарядов",
        "page_subtitle": "Входящие наряды",
        "title": "Входящие наряды",
    })


@login_required
def accept(request, plan_id):
    access = AccessManager(request.user)
    source_plan = get_object_or_404(DayPlan, pk=plan_id)
    user_unit = request.user.profile.unit

    if not access.can_plan("accept_incoming"):
        messages.error(request, "Нет доступа")
        return redirect("plan:incoming")

    logger.info("\n=== ACCEPT ===")
    logger.info(f"source: id={source_plan.id}, date={source_plan.date}, duty={source_plan.duty_type.name}")
    logger.info(
        f"source.unit={source_plan.unit.name if source_plan.unit else 'None'}, "
        f"type={source_plan.type}, status={source_plan.status}"
    )

    if source_plan.unit != user_unit or source_plan.type != "incoming" or source_plan.status != "pending":
        logger.warning("Не может быть принято")
        messages.error(request, "Это назначение не может быть принято")
        return redirect("plan:incoming")

    PlanService.accept_incoming_plan(source_plan, request.user)

    messages.success(request, f"Назначение на {source_plan.date} принято")
    return redirect("plan:incoming")