from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional

from django.db import transaction
from django.db.models import Q

from access_control.services import AccessManager
from core.services.assignment_service import AssignmentService
from duty_plans.models import DayPlan, DutyAssignment, MonthlySchedule
from people.models import Person


@dataclass(frozen=True)
class PersonCandidate:
    person: Person
    month_count: int
    same_duty_count: int
    recent_penalty: int
    score: int
    reason: str


class AssignmentAutomationService:
    MODE_FILL_ONLY = "fill_only"
    MODE_REPLACE_ALL = "replace_all"

    MONTH_ASSIGNMENT_WEIGHT = 10
    SAME_DUTY_WEIGHT = 5
    RECENT_ASSIGNMENT_PENALTY = 20
    CONSECUTIVE_DAY_PENALTY = 30

    @classmethod
    def preview_assignments(
        cls,
        *,
        user,
        year: int,
        month: int,
        mode: str = MODE_FILL_ONLY,
        only_understaffed: bool = True,
    ) -> dict:
        access = AccessManager(user)
        if not access.can_assignment("view"):
            raise PermissionError("Нет прав на просмотр назначений")

        user_unit = user.profile.unit
        month_start = date(year, month, 1)

        schedule = MonthlySchedule.objects.filter(
            month=month_start,
            unit=user_unit,
        ).first()

        if not schedule:
            return {
                "mode": mode,
                "mode_label": cls._mode_label(mode),
                "total_plans": 0,
                "changed_plans": 0,
                "total_new_assignments": 0,
                "suggestions": [],
                "summary": cls._build_empty_summary(mode),
            }

        plans = (
            schedule.days
            .filter(Q(type="own") | Q(type="incoming", status="accepted"))
            .select_related("unit", "duty_type", "parent")
            .prefetch_related("assignments__person", "children")
            .order_by("date", "duty_type__name")
        )

        suggestions = []
        per_person_month = cls._build_person_month_load(year=year, month=month, unit=user_unit)
        per_person_same_duty = cls._build_person_same_duty_load(year=year, month=month, unit=user_unit)

        for plan in plans:
            if not AssignmentService.can_assign_plan(plan, user):
                continue

            required = plan.duty_type.required_people or 0
            current_assignments = list(plan.assignments.select_related("person"))
            current_count = len(current_assignments)

            if mode == cls.MODE_FILL_ONLY:
                need = max(required - current_count, 0)
                if only_understaffed and need <= 0:
                    continue
            else:
                need = required
                if only_understaffed and current_count >= required:
                    continue

            available_people, assigned_ids, unavailable = AssignmentService.get_available_people_for_plan(
                plan, user_unit
            )

            available_people = cls._exclude_same_day_busy_people(
                plan=plan,
                people=list(available_people),
            )

            candidates: List[PersonCandidate] = []
            for person in available_people:
                month_count = per_person_month[person.id]
                same_duty_count = per_person_same_duty[(person.id, plan.duty_type_id)]
                recent_penalty = cls._recent_penalty(person=person, target_date=plan.date)

                score = (
                    month_count * cls.MONTH_ASSIGNMENT_WEIGHT
                    + same_duty_count * cls.SAME_DUTY_WEIGHT
                    + recent_penalty
                )

                reason = (
                    f"score={score}; month={month_count}; "
                    f"same_duty={same_duty_count}; recent_penalty={recent_penalty}"
                )

                candidates.append(
                    PersonCandidate(
                        person=person,
                        month_count=month_count,
                        same_duty_count=same_duty_count,
                        recent_penalty=recent_penalty,
                        score=score,
                        reason=reason,
                    )
                )

            candidates.sort(
                key=lambda x: (
                    x.score,
                    x.month_count,
                    x.same_duty_count,
                    x.person.last_name,
                    x.person.first_name,
                )
            )

            chosen_people = [c.person for c in candidates[:need]]

            suggestions.append({
                "plan_id": plan.id,
                "date": plan.date,
                "duty_name": plan.duty_type.name,
                "unit_name": plan.unit.name if plan.unit else "—",
                "required_people": required,
                "current_count": current_count,
                "need": need,
                "current_people": [
                    {
                        "id": a.person.id,
                        "name": a.person.full_name(),
                    }
                    for a in current_assignments
                ],
                "selected_people": [
                    {
                        "id": person.id,
                        "name": person.full_name(),
                    }
                    for person in chosen_people
                ],
                "candidate_debug": [
                    {
                        "id": c.person.id,
                        "name": c.person.full_name(),
                        "score": c.score,
                        "month_count": c.month_count,
                        "same_duty_count": c.same_duty_count,
                        "recent_penalty": c.recent_penalty,
                    }
                    for c in candidates[:10]
                ],
                "unavailable_count": len(unavailable),
                "changed": len(chosen_people) > 0 or (mode == cls.MODE_REPLACE_ALL and current_count > 0),
            })

        summary = cls._build_preview_summary(mode=mode, suggestions=suggestions)

        return {
            "mode": mode,
            "mode_label": cls._mode_label(mode),
            "total_plans": len(suggestions),
            "changed_plans": summary["changed_plans"],
            "total_new_assignments": summary["total_new_assignments"],
            "suggestions": suggestions,
            "summary": summary,
        }

    @classmethod
    def apply_assignments(
        cls,
        *,
        user,
        year: int,
        month: int,
        mode: str = MODE_FILL_ONLY,
        only_understaffed: bool = True,
    ) -> dict:
        preview = cls.preview_assignments(
            user=user,
            year=year,
            month=month,
            mode=mode,
            only_understaffed=only_understaffed,
        )

        with transaction.atomic():
            for item in preview["suggestions"]:
                if not item["changed"]:
                    continue

                plan = DayPlan.objects.select_related("unit", "duty_type").get(pk=item["plan_id"])

                if mode == cls.MODE_REPLACE_ALL:
                    plan.assignments.all().delete()

                selected_ids = [person["id"] for person in item["selected_people"]]
                if not selected_ids:
                    continue

                people = Person.objects.filter(id__in=selected_ids)

                for person in people:
                    can_assign, _error = AssignmentService.can_assign_to_plan(plan, user, person)
                    if not can_assign:
                        continue

                    DutyAssignment.objects.get_or_create(
                        day_plan=plan,
                        person=person,
                        defaults={"assigned_by": user},
                    )

        return preview

    @classmethod
    def _mode_label(cls, mode: str) -> str:
        if mode == cls.MODE_REPLACE_ALL:
            return "Пересобрать полностью"
        return "Только дозаполнить"

    @classmethod
    def _build_empty_summary(cls, mode: str) -> dict:
        return {
            "kind": "preview",
            "mode": mode,
            "mode_label": cls._mode_label(mode),
            "total_plans": 0,
            "changed_plans": 0,
            "total_new_assignments": 0,
            "unit_rows": [],
            "day_rows": [],
        }

    @classmethod
    def _build_preview_summary(cls, *, mode: str, suggestions: list) -> dict:
        per_day = Counter()
        per_duty = Counter()
        total_new_assignments = 0
        changed_plans = 0

        for item in suggestions:
            if item["changed"]:
                changed_plans += 1

            added = len(item["selected_people"])
            total_new_assignments += added
            per_day[item["date"].strftime("%d.%m.%Y")] += added
            per_duty[item["duty_name"]] += added

        day_rows = [
            {"day": day, "count": count}
            for day, count in per_day.most_common()
        ]

        duty_rows = [
            {"duty_name": duty_name, "count": count}
            for duty_name, count in per_duty.most_common()
        ]

        return {
            "kind": "preview",
            "mode": mode,
            "mode_label": cls._mode_label(mode),
            "total_plans": len(suggestions),
            "changed_plans": changed_plans,
            "total_new_assignments": total_new_assignments,
            "day_rows": day_rows,
            "duty_rows": duty_rows,
        }

    @staticmethod
    def _build_person_month_load(*, year: int, month: int, unit) -> defaultdict:
        result = defaultdict(int)

        rows = DutyAssignment.objects.filter(
            day_plan__date__year=year,
            day_plan__date__month=month,
            person__unit=unit,
        ).values_list("person_id", flat=True)

        for person_id in rows:
            result[person_id] += 1

        return result

    @staticmethod
    def _build_person_same_duty_load(*, year: int, month: int, unit) -> defaultdict:
        result = defaultdict(int)

        rows = DutyAssignment.objects.filter(
            day_plan__date__year=year,
            day_plan__date__month=month,
            person__unit=unit,
        ).values_list("person_id", "day_plan__duty_type_id")

        for person_id, duty_type_id in rows:
            result[(person_id, duty_type_id)] += 1

        return result

    @staticmethod
    def _exclude_same_day_busy_people(*, plan: DayPlan, people: List[Person]) -> List[Person]:
        if not people:
            return []

        person_ids = [p.id for p in people]

        busy_ids = set(
            DutyAssignment.objects.filter(
                day_plan__date=plan.date,
                person_id__in=person_ids,
            ).exclude(day_plan=plan).values_list("person_id", flat=True)
        )

        return [p for p in people if p.id not in busy_ids]

    @classmethod
    def _recent_penalty(cls, *, person: Person, target_date: date) -> int:
        yesterday = target_date - timedelta(days=1)
        two_days_ago = target_date - timedelta(days=2)

        assigned_dates = set(
            DutyAssignment.objects.filter(
                person=person,
                day_plan__date__in=[yesterday, two_days_ago],
            ).values_list("day_plan__date", flat=True)
        )

        penalty = 0
        if yesterday in assigned_dates:
            penalty += cls.RECENT_ASSIGNMENT_PENALTY
        if yesterday in assigned_dates and two_days_ago in assigned_dates:
            penalty += cls.CONSECUTIVE_DAY_PENALTY

        return penalty