"""
Сервис для работы с назначениями на наряды
"""
import calendar as cal
from datetime import date
from django.shortcuts import redirect
from django.urls import reverse

from duty_plans.models import MonthlySchedule, DayPlan
from people.models import Person
from access_control.services import AccessManager


class AssignmentService:
    @staticmethod
    def get_user_schedule(user_unit, year, month):
        return MonthlySchedule.objects.filter(
            month__year=year,
            month__month=month,
            unit=user_unit
        ).first()

    @staticmethod
    def get_prev_month(year, month):
        if month == 1:
            return year - 1, 12
        return year, month - 1

    @staticmethod
    def get_next_month(year, month):
        if month == 12:
            return year + 1, 1
        return year, month + 1

    @staticmethod
    def redirect_to_calendar(plan):
        return redirect(
            f"{reverse('assignment:calendar')}?year={plan.date.year}&month={plan.date.month}"
        )

    @staticmethod
    def build_calendar_context(user, year, month, today):
        access = AccessManager(user)
        user_unit = user.profile.unit

        prev_year, prev_month = AssignmentService.get_prev_month(year, month)
        next_year, next_month = AssignmentService.get_next_month(year, month)

        schedule = AssignmentService.get_user_schedule(user_unit, year, month)

        if not schedule:
            return {
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
                "can_view_assignments": access.can_assignment("view"),
            }

        day_plans = (
            DayPlan.objects
            .filter(schedule=schedule)
            .select_related("duty_type", "unit")
            .prefetch_related(
                "assignments",
                "assignments__person",
                "assignments__person__rank",
                "assignments__person__unit",
                "children",
            )
            .distinct()
        )

        raw_calendar_data = AssignmentService.build_calendar_data(day_plans, user, year, month)

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

        cal_obj = cal.Calendar(firstweekday=0)
        weeks = []

        for week in cal_obj.monthdatescalendar(year, month):
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

        return {
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
            "schedule": schedule,
            "total_plans": total_plans,
            "total_assigned": total_assigned,
            "needs_attention": needs_attention,
            "fully_staffed": fully_staffed,
            "active_tab": "assignments",
            "page_title": "Назначения сотрудников",
            "page_subtitle": "Календарь назначений",
            "title": "Назначения сотрудников",
            "can_view_assignments": access.can_assignment("view"),
        }

    @staticmethod
    def build_calendar_data(day_plans, user, year, month):
        access = AccessManager(user)
        user_unit = user.profile.unit

        last_day = cal.monthrange(year, month)[1]
        dates = [date(year, month, day) for day in range(1, last_day + 1)]

        plans_by_date = {}
        for plan in day_plans:
            if plan.date not in plans_by_date:
                plans_by_date[plan.date] = []
            plans_by_date[plan.date].append(plan)

        calendar_data = []
        for day in dates:
            day_data = {
                "date": day,
                "weekday": day.strftime("%a"),
                "plans": []
            }

            plans = plans_by_date.get(day, [])

            for plan in plans:
                required = plan.duty_type.required_people or 0
                is_own_unit = plan.unit_id == user_unit.id

                assignments, assignments_count = AssignmentService.get_plan_assignments(plan, is_own_unit)

                status, status_text = AssignmentService.get_plan_status(
                    plan, is_own_unit, assignments_count, required
                )

                unit_display = AssignmentService.get_unit_display(plan, is_own_unit)
                assigned_people = AssignmentService.format_assigned_people(assignments)

                can_assign = AssignmentService.can_assign_plan(plan, user)
                can_unassign = AssignmentService.can_unassign_plan(plan, user)
                can_manage = can_assign or can_unassign

                day_data["plans"].append({
                    "plan_id": plan.id,
                    "duty_name": plan.duty_type.name,
                    "required_people": required,
                    "unit_name": unit_display,
                    "unit_id": plan.unit.id if plan.unit else None,
                    "plan_type": plan.type,
                    "status": status,
                    "status_text": status_text,
                    "assignments": assigned_people,
                    "assigned_count": assignments_count,
                    "is_own_unit": is_own_unit,
                    "is_delegated": AssignmentService.is_plan_delegated(plan, is_own_unit),
                    "can_manage": can_manage,
                    "manage_url": reverse("assignment:get_people", args=[plan.id]) if can_manage else "",
                })

            day_data["plans"].sort(key=lambda x: (x["status"] != "unassigned", x["duty_name"]))
            calendar_data.append(day_data)

        return calendar_data

    @staticmethod
    def get_plan_assignments(plan, is_own_unit):
        if is_own_unit:
            assignments = plan.assignments.select_related("person", "person__rank", "person__unit")
            return assignments, assignments.count()

        for child_plan in plan.children.all():
            child_assignments = child_plan.assignments.select_related("person", "person__rank", "person__unit")
            if child_assignments.exists():
                return child_assignments, child_assignments.count()

        return [], 0

    @staticmethod
    def get_plan_status(plan, is_own_unit, assignments_count, required):
        has_children = plan.children.exists()
        child_pending = plan.children.filter(status="pending").exists() or plan.children.filter(child_status="pending").exists()

        if not is_own_unit:
            if assignments_count > 0:
                if assignments_count >= required:
                    return "completed", f"✅ Полностью назначен ({assignments_count}/{required})"
                return "partial", f"🔄 Частично назначен ({assignments_count}/{required})"
            return "delegated", "📎 Делегирован дочернему подразделению"

        if plan.type == "incoming" and has_children and child_pending:
            return "delegated", "📎 Делегирован дочернему подразделению (ожидает назначения)"

        if assignments_count == 0:
            return "unassigned", "⚠️ Требуется назначение"

        if assignments_count >= required:
            return "completed", f"✅ Полностью назначен ({assignments_count}/{required})"

        return "partial", f"🔄 Частично назначен ({assignments_count}/{required})"

    @staticmethod
    def get_unit_display(plan, is_own_unit):
        if not is_own_unit:
            return f"📎 {plan.unit.name} (дочернее)"
        if plan.type == "incoming" and plan.parent:
            return f"📎 {plan.unit.name} (от {plan.parent.unit.name})"
        return plan.unit.name

    @staticmethod
    def is_plan_delegated(plan, is_own_unit):
        if not is_own_unit:
            return True
        child_pending = plan.children.filter(status="pending").exists() or plan.children.filter(child_status="pending").exists()
        return plan.type == "incoming" and child_pending

    @staticmethod
    def format_assigned_people(assignments):
        result = []
        for a in assignments:
            result.append({
                "id": a.id,
                "person": a.person,
                "full_name": a.person.full_name(),
                "last_name": a.person.last_name,
                "rank_name": a.person.rank.name if a.person.rank else "",
                "unit_name": a.person.unit.name if a.person.unit else "",
            })
        return result

    @staticmethod
    def build_people_modal_data(plan, user):
        user_unit = user.profile.unit
        available, assigned_ids, unavailable = AssignmentService.get_available_people_for_plan(plan, user_unit)

        return {
            "plan_id": plan.id,
            "duty_name": plan.duty_type.name,
            "unit_name": plan.unit.name if plan.unit else "—",
            "date": plan.date.strftime("%d.%m.%Y"),
            "required_people": plan.duty_type.required_people or 0,
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
        }

    @staticmethod
    def get_available_people_for_plan(plan, user_unit):
        all_people = Person.objects.filter(unit=plan.unit).select_related("rank", "unit")

        cleared = Person.objects.filter(
            unit=plan.unit,
            clearances__duty_type=plan.duty_type
        ).distinct()

        exempted_ids = set(
            Person.objects.filter(
                exemptions__date_from__lte=plan.date,
                exemptions__date_to__gte=plan.date
            ).values_list("id", flat=True).distinct()
        )

        assigned_ids = set(plan.assignments.values_list("person_id", flat=True))

        available = cleared.exclude(id__in=list(assigned_ids)).exclude(id__in=list(exempted_ids))

        cleared_ids = set(cleared.values_list("id", flat=True))

        unavailable = []
        for person in all_people:
            if person.id in assigned_ids:
                unavailable.append({
                    "id": person.id,
                    "name": person.full_name(),
                    "rank": person.rank.name if person.rank else "",
                    "reason": "Уже назначен",
                })
            elif person.id in exempted_ids:
                unavailable.append({
                    "id": person.id,
                    "name": person.full_name(),
                    "rank": person.rank.name if person.rank else "",
                    "reason": "Освобождён",
                })
            elif person.id not in cleared_ids:
                unavailable.append({
                    "id": person.id,
                    "name": person.full_name(),
                    "rank": person.rank.name if person.rank else "",
                    "reason": "Нет допуска",
                })

        return available, assigned_ids, unavailable

    @staticmethod
    def business_can_edit_plan(plan, user_unit):
        if plan.unit_id != user_unit.id:
            return False, "Наряд делегирован дочернему подразделению"

        if plan.children.filter(status="pending").exists() or plan.children.filter(child_status="pending").exists():
            return False, "Наряд делегирован дочернему подразделению"

        return True, ""

    @staticmethod
    def can_edit_plan(plan, user):
        access = AccessManager(user)
        user_unit = user.profile.unit

        if not (access.can_assignment("assign", plan) or access.can_assignment("unassign", plan)):
            return False, "Нет прав на управление назначениями"

        return AssignmentService.business_can_edit_plan(plan, user_unit)

    @staticmethod
    def can_assign_plan(plan, user):
        access = AccessManager(user)
        user_unit = user.profile.unit

        if not access.can_assignment("assign", plan):
            return False

        can_edit, _ = AssignmentService.business_can_edit_plan(plan, user_unit)
        return can_edit

    @staticmethod
    def can_unassign_plan(plan, user):
        access = AccessManager(user)
        user_unit = user.profile.unit

        if not access.can_assignment("unassign", plan):
            return False

        can_edit, _ = AssignmentService.business_can_edit_plan(plan, user_unit)
        return can_edit

    @staticmethod
    def can_assign_to_plan(plan, user, person):
        user_unit = user.profile.unit

        can_edit, error_msg = AssignmentService.can_edit_plan(plan, user)
        if not can_edit:
            return False, error_msg

        if person.unit_id != plan.unit_id:
            return False, "Сотрудник не из этого подразделения"

        if not person.clearances.filter(duty_type=plan.duty_type).exists():
            return False, "Сотрудник не имеет допуска к этому типу наряда"

        if person.exemptions.filter(date_from__lte=plan.date, date_to__gte=plan.date).exists():
            return False, "Сотрудник освобождён в этот день"

        if plan.assignments.count() >= (plan.duty_type.required_people or 0):
            return False, f"Превышен лимит назначений (максимум {plan.duty_type.required_people} чел.)"

        return True, ""