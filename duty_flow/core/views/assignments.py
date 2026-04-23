from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from access_control.services import AccessManager
from core.services.assignment_automation_service import AssignmentAutomationService
from core.services.assignment_service import AssignmentService
from duty_plans.models import DayPlan, DutyAssignment
from people.models import Person


AUTO_ASSIGN_PREVIEW_SESSION_KEY = "assignment_auto_preview"


def _calendar_redirect(year: int, month: int):
    return redirect(f"{reverse('assignment:calendar')}?year={year}&month={month}")


def _build_auto_params(request):
    return {
        "mode": request.POST.get("auto_mode", AssignmentAutomationService.MODE_FILL_ONLY),
        "only_understaffed": request.POST.get("auto_only_understaffed") == "1",
    }


def _serialize_auto_preview(preview: dict) -> dict:
    serialized = {
        "mode": preview.get("mode"),
        "mode_label": preview.get("mode_label"),
        "total_plans": preview.get("total_plans"),
        "changed_plans": preview.get("changed_plans"),
        "total_new_assignments": preview.get("total_new_assignments"),
        "summary": preview.get("summary"),
        "suggestions": [],
    }

    for item in preview.get("suggestions", []):
        serialized["suggestions"].append({
            "plan_id": item.get("plan_id"),
            "date": item["date"].isoformat() if item.get("date") else None,
            "duty_name": item.get("duty_name"),
            "unit_name": item.get("unit_name"),
            "required_people": item.get("required_people"),
            "current_count": item.get("current_count"),
            "need": item.get("need"),
            "current_people": item.get("current_people", []),
            "selected_people": item.get("selected_people", []),
            "candidate_debug": item.get("candidate_debug", []),
            "unavailable_count": item.get("unavailable_count"),
            "changed": item.get("changed", False),
        })

    return serialized


def _save_auto_preview(request, year: int, month: int, params: dict, preview: dict):
    request.session[AUTO_ASSIGN_PREVIEW_SESSION_KEY] = {
        "year": year,
        "month": month,
        "params": params,
        **_serialize_auto_preview(preview),
    }
    request.session.modified = True


def _get_auto_preview(request, year: int, month: int):
    preview = request.session.get(AUTO_ASSIGN_PREVIEW_SESSION_KEY)
    if not preview:
        return None
    if preview.get("year") != year or preview.get("month") != month:
        return None
    return preview


def _clear_auto_preview(request):
    if AUTO_ASSIGN_PREVIEW_SESSION_KEY in request.session:
        request.session.pop(AUTO_ASSIGN_PREVIEW_SESSION_KEY, None)
        request.session.modified = True


@login_required
def calendar(request):
    access = AccessManager(request.user)

    if not access.can_assignment("view"):
        messages.error(request, "Нет доступа к календарю назначений")
        return render(request, "app/assignments/calendar.html", {
            "year": datetime.now().date().year,
            "month": datetime.now().date().month,
            "now_year": datetime.now().date().year,
            "now_month": datetime.now().date().month,
            "prev_year": datetime.now().date().year,
            "prev_month": datetime.now().date().month,
            "next_year": datetime.now().date().year,
            "next_month": datetime.now().date().month,
            "month_name": datetime.now().date().strftime("%B %Y"),
            "calendar_data": [],
            "has_schedule": False,
            "total_plans": 0,
            "total_assigned": 0,
            "needs_attention": 0,
            "fully_staffed": 0,
            "active_tab": "assignments",
            "page_title": "Назначения сотрудников",
            "page_subtitle": "Календарь назначений",
            "title": "Назначения сотрудников",
            "auto_preview": None,
            "current_auto_params": {
                "mode": AssignmentAutomationService.MODE_FILL_ONLY,
                "only_understaffed": True,
            },
        })

    today = datetime.now().date()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    context = AssignmentService.build_calendar_context(
        user=request.user,
        year=year,
        month=month,
        today=today,
    )

    saved_preview = _get_auto_preview(request, year, month)
    current_auto_params = saved_preview["params"] if saved_preview else {
        "mode": AssignmentAutomationService.MODE_FILL_ONLY,
        "only_understaffed": True,
    }

    context["auto_preview"] = saved_preview
    context["current_auto_params"] = current_auto_params

    return render(request, "app/assignments/calendar.html", context)


@login_required
def get_available_people(request, plan_id):
    plan = get_object_or_404(DayPlan, pk=plan_id)

    can_edit, error_msg = AssignmentService.can_edit_plan(plan, request.user)
    if not can_edit:
        return JsonResponse({"error": error_msg}, status=403)

    data = AssignmentService.build_people_modal_data(plan, request.user)
    return JsonResponse(data)


@login_required
def assign_person(request, plan_id):
    plan = get_object_or_404(DayPlan, pk=plan_id)
    person_id = request.POST.get("person_id")

    if not person_id:
        messages.error(request, "Сотрудник не выбран")
        return AssignmentService.redirect_to_calendar(plan)

    person = get_object_or_404(Person, pk=person_id)

    can_assign, error_msg = AssignmentService.can_assign_to_plan(plan, request.user, person)
    if not can_assign:
        messages.error(request, error_msg)
        return AssignmentService.redirect_to_calendar(plan)

    _, created = DutyAssignment.objects.get_or_create(
        day_plan=plan,
        person=person,
        defaults={"assigned_by": request.user}
    )

    if created:
        messages.success(request, f"Сотрудник {person.full_name()} назначен")
    else:
        messages.warning(request, f"Сотрудник {person.full_name()} уже назначен")

    return AssignmentService.redirect_to_calendar(plan)


@login_required
def unassign_person(request, assignment_id):
    assignment = get_object_or_404(DutyAssignment, pk=assignment_id)
    plan = assignment.day_plan

    if not AssignmentService.can_unassign_plan(plan, request.user):
        messages.error(request, "Нет прав на снятие назначения")
        return AssignmentService.redirect_to_calendar(plan)

    person_name = assignment.person.full_name()
    assignment.delete()
    messages.success(request, f"Назначение сотрудника {person_name} снято")

    return AssignmentService.redirect_to_calendar(plan)


@login_required
def preview_auto_assign(request):
    access = AccessManager(request.user)
    if not access.can_assignment("view"):
        messages.error(request, "Нет прав")
        return _calendar_redirect(datetime.now().date().year, datetime.now().date().month)

    today = datetime.now().date()
    year = int(request.POST.get("year", today.year))
    month = int(request.POST.get("month", today.month))
    params = _build_auto_params(request)

    try:
        preview = AssignmentAutomationService.preview_assignments(
            user=request.user,
            year=year,
            month=month,
            mode=params["mode"],
            only_understaffed=params["only_understaffed"],
        )
    except PermissionError as exc:
        messages.error(request, str(exc))
        return _calendar_redirect(year, month)
    except Exception as exc:
        messages.error(request, f"Ошибка предпросмотра автоназначения: {exc}")
        return _calendar_redirect(year, month)

    _save_auto_preview(request, year, month, params, preview)
    messages.success(
        request,
        (
            f"Предпросмотр автоназначения построен ({preview['mode_label']}): "
            f"{preview['changed_plans']} планов, {preview['total_new_assignments']} новых назначений"
        )
    )
    return _calendar_redirect(year, month)


@login_required
def apply_auto_assign(request):
    access = AccessManager(request.user)
    if not access.can_assignment("view"):
        messages.error(request, "Нет прав")
        return _calendar_redirect(datetime.now().date().year, datetime.now().date().month)

    today = datetime.now().date()
    year = int(request.POST.get("year", today.year))
    month = int(request.POST.get("month", today.month))

    saved_preview = _get_auto_preview(request, year, month)
    params = saved_preview["params"] if saved_preview else _build_auto_params(request)

    try:
        result = AssignmentAutomationService.apply_assignments(
            user=request.user,
            year=year,
            month=month,
            mode=params["mode"],
            only_understaffed=params["only_understaffed"],
        )
    except Exception as exc:
        messages.error(request, f"Ошибка применения автоназначения: {exc}")
        return _calendar_redirect(year, month)

    _save_auto_preview(request, year, month, params, result)
    messages.success(
        request,
        (
            f"Автоназначение выполнено ({result['mode_label']}): "
            f"{result['changed_plans']} планов, {result['total_new_assignments']} новых назначений"
        )
    )
    return _calendar_redirect(year, month)


@login_required
def clear_auto_assign_preview(request):
    today = datetime.now().date()
    year = int(request.POST.get("year", today.year))
    month = int(request.POST.get("month", today.month))

    _clear_auto_preview(request)
    messages.success(request, "Предпросмотр автоназначения очищен")
    return _calendar_redirect(year, month)