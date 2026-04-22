from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now

from access_control.services import AccessManager
from access_control.services.labels import build_unit_path_label
from duty_plans.models import MonthlySchedule, DayPlan
from duty_plans.forms import MonthlyScheduleForm
from core.services.plan_service import PlanService
from core.services.plan_automation_service import PlanAutomationService

import logging

logger = logging.getLogger(__name__)


def apply_plan_access_to_form(form, access_manager, action: str):
    visible_fields = set(access_manager.visible_plan_fields(action))
    editable_fields = set(access_manager.editable_plan_fields(action))

    for field_name in tuple(form.fields.keys()):
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
    schedule = get_object_or_404(
        MonthlySchedule.objects.select_related("unit", "unit__parent", "unit__unit_type"),
        pk=pk
    )

    base_unit = schedule.unit

    if not access.can_plan("manage_days", schedule):
        messages.error(request, "Нет прав")
        return redirect("plan:list")

    allowed_delegate_units = access.allowed_delegate_units_for_plan_days(schedule).exclude(id=base_unit.id)

    dates, duty_types, plans_dict, incoming_days = PlanService.build_table_data(schedule, base_unit)

    logger.info(
        "PLAN DAYS schedule_id=%s unit=%s user=%s duty_types=%s dates=%s",
        schedule.id,
        schedule.unit.name,
        request.user.username,
        len(duty_types),
        len(dates),
    )

    delegate_units = [
        {
            "id": unit.id,
            "label": build_unit_path_label(unit),
        }
        for unit in allowed_delegate_units
    ]

    weekday_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    date_headers = []
    for current_date in dates:
        weekday_index = current_date.weekday()
        date_headers.append({
            "date": current_date,
            "day": current_date.day,
            "weekday_short": weekday_names[weekday_index],
            "is_weekend": weekday_index >= 5,
        })

    if request.method == "POST":
        PlanService.process_post_data(
            schedule=schedule,
            post_data=request.POST,
            plans_dict=plans_dict,
            incoming_days=incoming_days,
            base_unit=base_unit,
            user=request.user,
            allowed_delegate_units=allowed_delegate_units,
        )
        messages.success(request, "Сохранено")
        return redirect("plan:days", pk=schedule.pk)

    table = PlanService.build_table_rows(
        dates=dates,
        duty_types=duty_types,
        plans_dict=plans_dict,
        incoming_days=incoming_days,
        base_unit=base_unit,
        allowed_delegate_units=allowed_delegate_units,
    )

    distribution_preview = PlanAutomationService.preview_distribution(
        schedule=schedule,
        user=request.user,
        mode=PlanAutomationService.MODE_BALANCED_STRUCTURE,
        only_empty=False,
    )
    distribution_summary = distribution_preview.get("summary")

    return render(request, "app/plans/days.html", {
        "schedule": schedule,
        "dates": dates,
        "date_headers": date_headers,
        "table": table,
        "delegate_units": delegate_units,
        "base_unit": base_unit,
        "active_tab": "plans",
        "page_title": "Планы нарядов",
        "page_subtitle": "Таблица нарядов по дням",
        "title": schedule.name or str(schedule),
        "duty_types_count": len(duty_types),
        "dates_count": len(dates),
        "incoming_days": incoming_days,
        "distribution_summary": distribution_summary,
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
            grouped[source_schedule] = {"source_schedule": source_schedule, "items": [], "count": 0}

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

    if source_plan.unit != user_unit or source_plan.type != "incoming" or source_plan.status != "pending":
        messages.error(request, "Это назначение не может быть принято")
        return redirect("plan:incoming")

    PlanService.accept_incoming_plan(source_plan, request.user)
    messages.success(request, f"Назначение на {source_plan.date} принято")
    return redirect("plan:incoming")


@login_required
def auto_distribute(request, pk):
    access = AccessManager(request.user)

    schedule = get_object_or_404(
        MonthlySchedule.objects.select_related("unit", "unit__parent", "unit__unit_type"),
        pk=pk
    )

    if not access.can_plan("manage_days", schedule):
        messages.error(request, "Нет прав на автоматическое распределение")
        return redirect("plan:days", pk=pk)

    mode = request.POST.get("auto_mode", PlanAutomationService.MODE_BALANCED)
    only_empty = request.POST.get("auto_only_empty") == "1"

    logger.info(
        "AUTO DISTRIBUTE start schedule_id=%s unit=%s user=%s mode=%s normalized_mode=%s only_empty=%s",
        schedule.id,
        schedule.unit.name,
        request.user.username,
        mode,
        PlanAutomationService.normalize_mode(mode),
        only_empty,
    )

    try:
        preview = PlanAutomationService.preview_distribution(
            schedule=schedule,
            user=request.user,
            mode=mode,
            only_empty=only_empty,
        )
    except PermissionError as exc:
        logger.warning("AUTO DISTRIBUTE denied schedule_id=%s: %s", schedule.id, exc)
        messages.error(request, str(exc))
        return redirect("plan:days", pk=pk)
    except Exception as exc:
        logger.exception("AUTO DISTRIBUTE preview failed schedule_id=%s", schedule.id)
        messages.error(request, f"Ошибка предварительного анализа: {exc}")
        return redirect("plan:days", pk=pk)

    logger.info(
        "AUTO DISTRIBUTE preview schedule_id=%s total=%s changed=%s",
        schedule.id,
        preview["total_count"],
        preview["changed_count"],
    )

    for item in preview.get("duty_debug", {}).values():
        logger.info(
            "AUTO DISTRIBUTE duty=%s eligible=[%s] rejected=[%s]",
            item["duty_name"],
            ", ".join(item["eligible_units"]) or "-",
            ", ".join(item["rejected_units"]) or "-",
        )

    if preview["total_count"] == 0:
        messages.warning(
            request,
            (
                "Автораспределению нечего обрабатывать. "
                "Проверьте доступные типы нарядов и входящие принятые наряды."
            )
        )
        return redirect("plan:days", pk=pk)

    if preview["changed_count"] == 0:
        messages.info(
            request,
            (
                f"Подходящие ячейки найдены ({preview['total_count']}), "
                "но изменений не предложено."
            )
        )
        return redirect("plan:days", pk=pk)

    try:
        result = PlanAutomationService.apply_distribution(
            schedule=schedule,
            user=request.user,
            mode=mode,
            only_empty=only_empty,
        )
    except Exception as exc:
        logger.exception("AUTO DISTRIBUTE apply failed schedule_id=%s", schedule.id)
        messages.error(request, f"Ошибка применения автораспределения: {exc}")
        return redirect("plan:days", pk=pk)

    logger.info(
        "AUTO DISTRIBUTE done schedule_id=%s total=%s changed=%s",
        schedule.id,
        result["total_count"],
        result["changed_count"],
    )

    messages.success(
        request,
        (
            f"Автораспределение выполнено ({result['mode']}): "
            f"{result['changed_count']} изменений из {result['total_count']}"
        )
    )

    return redirect("plan:days", pk=pk)