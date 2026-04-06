from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now

from duty_plans.models import MonthlySchedule, DayPlan
from duty_plans.forms import MonthlyScheduleForm
from users_app.access_service import AccessService
from core.services.plan_service import PlanService

import logging

logger = logging.getLogger(__name__)


@login_required
def list(request):
    user_unit = request.user.profile.unit
    access = AccessService(request.user)

    schedules = (
        MonthlySchedule.objects
        .filter(unit=user_unit)
        .select_related("unit", "parent_schedule", "created_by")
        .order_by("-month")
    )

    search_query = request.GET.get("q", "").strip()
    if search_query:
        schedules = schedules.filter(name__icontains=search_query)

    return render(request, "app/plans/list.html", {
        "schedules": schedules,
        "active_tab": "plans",
        "page_title": "Планы нарядов",
        "page_subtitle": "Месячные расписания подразделения",
        "search_query": search_query,
        "can_add": True,
        "title": "Планы нарядов",
    })


@login_required
def add(request):
    user_unit = request.user.profile.unit

    if request.method == "POST":
        form = MonthlyScheduleForm(request.POST, user=request.user)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.unit = user_unit

            if not schedule.name:
                schedule.name = f"Расписание {schedule.month.strftime('%B %Y')}"

            schedule.save()
            messages.success(request, 'Расписание создано')
            return redirect("plan:detail", pk=schedule.pk)
    else:
        form = MonthlyScheduleForm(
            user=request.user,
            initial={"month": now().date().replace(day=1)}
        )

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
    schedule = get_object_or_404(
        MonthlySchedule.objects.select_related("unit", "parent_schedule", "created_by"),
        pk=pk
    )

    user_unit = request.user.profile.unit
    if schedule.unit != user_unit:
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
        "active_tab": "plans",
        "page_title": "Планы нарядов",
        "page_subtitle": "Карточка расписания",
        "title": schedule.name or str(schedule),
    })


@login_required
def edit(request, pk):
    schedule = get_object_or_404(MonthlySchedule, pk=pk)
    user_unit = request.user.profile.unit

    if schedule.unit != user_unit:
        messages.error(request, "Нет прав")
        return redirect("plan:list")

    if request.method == "POST":
        form = MonthlyScheduleForm(request.POST, instance=schedule, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Расписание обновлено")
            return redirect("plan:detail", pk=schedule.pk)
    else:
        form = MonthlyScheduleForm(instance=schedule, user=request.user)

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
    schedule = get_object_or_404(MonthlySchedule, pk=pk)
    access = AccessService(request.user)

    if schedule.unit != access.user_unit:
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
    schedule = get_object_or_404(MonthlySchedule, pk=pk)
    user_unit = request.user.profile.unit

    logger.info("\n" + "=" * 70)
    logger.info("=== DAYS() START ===")
    logger.info(f"Расписание: id={schedule.id}, month={schedule.month}, unit={schedule.unit.name}")
    logger.info(f"Пользователь: {request.user.username}, подразделение: {user_unit.name}")

    if schedule.unit != user_unit:
        logger.warning(f"Нет прав: расписание принадлежит {schedule.unit.name}")
        messages.error(request, "Нет прав")
        return redirect("plan:list")

    dates, duty_types, plans_dict, incoming_day, children = PlanService.build_table_data(schedule, user_unit)

    weekday_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    date_headers = []
    for date in dates:
        weekday_index = date.weekday()  # 0=Mon ... 6=Sun
        date_headers.append({
            "date": date,
            "day": date.day,
            "weekday_short": weekday_names[weekday_index],
            "is_weekend": weekday_index >= 5,
        })

    if request.method == "POST":
        logger.info("\n--- ОБРАБОТКА POST ЗАПРОСА ---")
        PlanService.process_post_data(
            schedule,
            request.POST,
            plans_dict,
            incoming_day,
            user_unit,
            request.user
        )
        messages.success(request, "Сохранено")
        return redirect("plan:days", pk=schedule.pk)

    table = PlanService.build_table_rows(dates, duty_types, plans_dict, incoming_day, user_unit)

    logger.info(f"\n--- ИТОГО СТРОК В ТАБЛИЦЕ: {len(table)} ---")
    logger.info("=" * 70 + "\n")

    return render(request, "app/plans/days.html", {
    "schedule": schedule,
    "dates": dates,
    "date_headers": date_headers,
    "table": table,
    "children": children,
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
    user_unit = request.user.profile.unit

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
    source_plan = get_object_or_404(DayPlan, pk=plan_id)
    user_unit = request.user.profile.unit

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