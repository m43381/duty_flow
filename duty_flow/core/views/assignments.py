from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from access_control.services import AccessManager
from duty_plans.models import DayPlan, DutyAssignment
from people.models import Person
from core.services.assignment_service import AssignmentService


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