from datetime import datetime, date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse

from duty_plans.models import DayPlan, DutyAssignment
from people.models import Person
from users_app.access_service import AccessService
from core.services.assignment_service import AssignmentService


def _get_prev_month(year: int, month: int):
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _get_next_month(year: int, month: int):
    if month == 12:
        return year + 1, 1
    return year, month + 1


from datetime import datetime, date
import calendar as pycalendar

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from duty_plans.models import DayPlan
from users_app.access_service import AccessService
from core.services.assignment_service import AssignmentService


def _get_prev_month(year: int, month: int):
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _get_next_month(year: int, month: int):
    if month == 12:
        return year + 1, 1
    return year, month + 1


@login_required
def calendar(request):
    access = AccessService(request.user)

    today = datetime.now().date()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    prev_year, prev_month = _get_prev_month(year, month)
    next_year, next_month = _get_next_month(year, month)

    user_schedule = AssignmentService.get_user_schedule(access.user_unit, year, month)

    if not user_schedule:
        return render(request, "app/assignments/calendar.html", {
            "year": year,
            "month": month,
            "now_year": today.year,
            "now_month": today.month,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "month_name": date(year, month, 1).strftime("%B %Y"),
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
        })

    day_plans = (
        DayPlan.objects
        .filter(schedule=user_schedule)
        .select_related("duty_type", "unit")
        .prefetch_related(
            "assignments",
            "assignments__person",
            "assignments__person__rank",
            "assignments__person__unit",
        )
        .distinct()
    )

    raw_calendar_data = AssignmentService.build_calendar_data(day_plans, year, month, access.user_unit)

    day_map = {}
    total_plans = 0
    total_assigned = 0
    needs_attention = 0
    fully_staffed = 0

    for day_data in raw_calendar_data:
        day_data["is_today"] = day_data["date"] == today
        day_data["is_weekend"] = day_data["date"].weekday() >= 5

        for plan in day_data.get("plans", []):
            total_plans += 1
            total_assigned += plan.get("assigned_count", 0)

            required_people = plan.get("required_people", 0)
            assigned_count = plan.get("assigned_count", 0)

            if required_people > 0 and assigned_count >= required_people:
                fully_staffed += 1
            else:
                needs_attention += 1

        day_map[day_data["date"]] = day_data

    cal = pycalendar.Calendar(firstweekday=0)  # ПН
    weeks = []

    for week in cal.monthdatescalendar(year, month):
        week_cells = []
        for day_date in week:
            if day_date.month != month:
                week_cells.append(None)
            else:
                week_cells.append(day_map.get(day_date, {
                    "date": day_date,
                    "plans": [],
                    "is_today": day_date == today,
                    "is_weekend": day_date.weekday() >= 5,
                }))
        weeks.append(week_cells)

    return render(request, "app/assignments/calendar.html", {
        "year": year,
        "month": month,
        "now_year": today.year,
        "now_month": today.month,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "month_name": date(year, month, 1).strftime("%B %Y"),
        "calendar_data": weeks,
        "has_schedule": True,
        "schedule": user_schedule,
        "total_plans": total_plans,
        "total_assigned": total_assigned,
        "needs_attention": needs_attention,
        "fully_staffed": fully_staffed,
        "active_tab": "assignments",
        "page_title": "Назначения сотрудников",
        "page_subtitle": "Календарь назначений",
        "title": "Назначения сотрудников",
    })


@login_required
def get_available_people(request, plan_id):
    """Получить доступных сотрудников (AJAX)"""
    plan = get_object_or_404(DayPlan, pk=plan_id)
    access = AccessService(request.user)

    can_edit, error_msg = AssignmentService.can_edit_plan(plan, access.user_unit)
    if not can_edit:
        return JsonResponse({"error": error_msg}, status=403)

    available, assigned_ids, unavailable = AssignmentService.get_available_people_for_plan(plan, access.user_unit)

    return JsonResponse({
        "plan_id": plan.id,
        "duty_name": plan.duty_type.name,
        "unit_name": plan.unit.name if plan.unit else "—",
        "date": plan.date.strftime("%d.%m.%Y"),
        "required_people": plan.duty_type.required_people,
        "current_count": plan.assignments.count(),
        "available": [
            {
                "id": p.id,
                "name": p.full_name(),
                "rank": p.rank.name if p.rank else "",
                "unit": p.unit.name if p.unit else "",
            }
            for p in available
        ],
        "assigned": [
            {
                "id": a.id,
                "name": a.person.full_name(),
                "rank": a.person.rank.name if a.person.rank else "",
                "unit": a.person.unit.name if a.person.unit else "",
            }
            for a in plan.assignments.select_related("person", "person__rank", "person__unit")
        ],
        "unavailable": unavailable,
    })


@login_required
def assign_person(request, plan_id):
    """Назначить сотрудника"""
    plan = get_object_or_404(DayPlan, pk=plan_id)
    person_id = request.POST.get("person_id")

    if not person_id:
        messages.error(request, "Сотрудник не выбран")
        return redirect(f"{reverse('assignment:calendar')}?year={plan.date.year}&month={plan.date.month}")

    person = get_object_or_404(Person, pk=person_id)
    access = AccessService(request.user)

    can_edit, error_msg = AssignmentService.can_edit_plan(plan, access.user_unit)
    if not can_edit:
        messages.error(request, error_msg)
        return redirect(f"{reverse('assignment:calendar')}?year={plan.date.year}&month={plan.date.month}")

    can_assign, error_msg = AssignmentService.can_assign_to_plan(plan, access.user_unit, person)
    if not can_assign:
        messages.error(request, error_msg)
        return redirect(f"{reverse('assignment:calendar')}?year={plan.date.year}&month={plan.date.month}")

    _, created = DutyAssignment.objects.get_or_create(
        day_plan=plan,
        person=person,
        defaults={"assigned_by": request.user}
    )

    if created:
        messages.success(request, f"Сотрудник {person.full_name()} назначен")
    else:
        messages.warning(request, f"Сотрудник {person.full_name()} уже назначен")

    return redirect(f"{reverse('assignment:calendar')}?year={plan.date.year}&month={plan.date.month}")


@login_required
def unassign_person(request, assignment_id):
    """Снять назначение"""
    assignment = get_object_or_404(DutyAssignment, pk=assignment_id)
    access = AccessService(request.user)
    plan = assignment.day_plan

    can_edit, error_msg = AssignmentService.can_edit_plan(plan, access.user_unit)
    if not can_edit:
        messages.error(request, error_msg)
        return redirect(f"{reverse('assignment:calendar')}?year={plan.date.year}&month={plan.date.month}")

    person_name = assignment.person.full_name()
    assignment.delete()
    messages.success(request, f"Назначение сотрудника {person_name} снято")

    return redirect(f"{reverse('assignment:calendar')}?year={plan.date.year}&month={plan.date.month}")