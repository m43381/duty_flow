from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, List, Optional, Tuple

from django.http import QueryDict

from access_control.services import AccessManager
from core.services.plan_service import PlanService
from duty_plans.models import DayPlan, DutyAssignment, MonthlySchedule
from duty_types.models import DutyType
from people.models import Person
from units.models import Unit


@dataclass(frozen=True)
class DistributionCandidate:
    unit: Unit
    capacity: int
    total_month_load: int
    same_duty_month_load: int
    score: int
    reason: str


class PlanAutomationService:
    """
    Автоматическое распределение нарядов по подразделениям.

    Важно:
    - сервис НЕ меняет напрямую дерево делегирования;
    - сервис только вычисляет, в какое подразделение поставить каждую ячейку;
    - применение результата идёт через существующий PlanService.process_post_data(...),
      чтобы не ломать текущую бизнес-логику.
    """

    MODE_PREFER_OWN = "prefer_own"
    MODE_BALANCED = "balanced"
    MODE_PREFER_CHILDREN = "prefer_children"

    BASE_LOAD_WEIGHT = 10
    SAME_DUTY_WEIGHT = 5
    SHORTAGE_PENALTY = 1000
    DELEGATION_PENALTY = 15
    OWN_UNIT_BONUS = 30
    PREFER_CHILDREN_BASE_PENALTY = 20

    @classmethod
    def preview_distribution(
        cls,
        *,
        schedule: MonthlySchedule,
        user,
        mode: str = MODE_BALANCED,
        only_empty: bool = False,
        selected_dates: Optional[Iterable[date]] = None,
        selected_duty_type_ids: Optional[Iterable[int]] = None,
    ) -> dict:
        """
        Возвращает предложения по распределению, но ничего не сохраняет.
        """
        access = AccessManager(user)
        if not access.can_plan("manage_days", schedule):
            raise PermissionError("Нет прав на автоматическое распределение")

        base_unit = schedule.unit
        allowed_delegate_units_qs = access.allowed_delegate_units_for_plan_days(schedule).exclude(
            id=base_unit.id
        )
        allowed_delegate_units = list(allowed_delegate_units_qs)

        dates, duty_types, plans_dict, incoming_days = PlanService.build_table_data(schedule, base_unit)

        selected_dates = set(selected_dates or dates)
        selected_duty_type_ids = set(selected_duty_type_ids or [dt.id for dt in duty_types])

        candidate_units = [base_unit, *allowed_delegate_units]

        unit_month_load = cls._build_unit_month_load(
            year=schedule.month.year,
            month=schedule.month.month,
            candidate_units=candidate_units,
        )
        unit_duty_month_load = cls._build_unit_duty_month_load(
            year=schedule.month.year,
            month=schedule.month.month,
            candidate_units=candidate_units,
        )

        suggestions = []
        mapping: Dict[Tuple[date, int], int] = {}

        for duty_type in duty_types:
            if duty_type.id not in selected_duty_type_ids:
                continue

            for current_date in dates:
                if current_date not in selected_dates:
                    continue

                existing_plan = plans_dict.get((current_date, duty_type.id))
                if only_empty and existing_plan is not None:
                    continue

                if not cls._is_editable_cell(
                    duty_type=duty_type,
                    current_date=current_date,
                    existing_plan=existing_plan,
                    incoming_days=incoming_days,
                    base_unit=base_unit,
                    allowed_delegate_units=allowed_delegate_units,
                ):
                    continue

                current_unit_id = existing_plan.unit_id if existing_plan else None
                current_unit_name = existing_plan.unit.name if existing_plan and existing_plan.unit else None

                candidates: List[DistributionCandidate] = []

                for unit in candidate_units:
                    capacity = cls._calculate_capacity(
                        unit=unit,
                        duty_type=duty_type,
                        target_date=current_date,
                    )

                    required_people = duty_type.required_people or 0

                    if capacity <= 0:
                        continue

                    # На старте исключаем заведомо непригодные подразделения
                    if required_people and capacity < required_people:
                        continue

                    total_month_load = unit_month_load[unit.id]
                    same_duty_month_load = unit_duty_month_load[(unit.id, duty_type.id)]

                    score, reason = cls._score_unit(
                        mode=mode,
                        unit=unit,
                        base_unit=base_unit,
                        capacity=capacity,
                        required_people=required_people,
                        total_month_load=total_month_load,
                        same_duty_month_load=same_duty_month_load,
                    )

                    candidates.append(
                        DistributionCandidate(
                            unit=unit,
                            capacity=capacity,
                            total_month_load=total_month_load,
                            same_duty_month_load=same_duty_month_load,
                            score=score,
                            reason=reason,
                        )
                    )

                candidates.sort(
                    key=lambda x: (
                        x.score,
                        x.total_month_load,
                        x.same_duty_month_load,
                        x.unit.name,
                    )
                )

                if not candidates:
                    suggestions.append({
                        "date": current_date,
                        "duty_type": duty_type,
                        "current_unit_id": current_unit_id,
                        "current_unit_name": current_unit_name,
                        "selected_unit_id": None,
                        "selected_unit_name": None,
                        "changed": False,
                        "reason": "Нет подходящего подразделения с доступной ёмкостью",
                        "candidates": [],
                    })
                    continue

                winner = candidates[0]

                suggestions.append({
                    "date": current_date,
                    "duty_type": duty_type,
                    "current_unit_id": current_unit_id,
                    "current_unit_name": current_unit_name,
                    "selected_unit_id": winner.unit.id,
                    "selected_unit_name": winner.unit.name,
                    "changed": current_unit_id != winner.unit.id,
                    "reason": winner.reason,
                    "candidates": candidates,
                })

                mapping[(current_date, duty_type.id)] = winner.unit.id

                # Важно: балансируем не только по данным БД, но и внутри текущего прогона,
                # чтобы алгоритм не выбирал один и тот же unit на все ячейки подряд.
                unit_month_load[winner.unit.id] += 1
                unit_duty_month_load[(winner.unit.id, duty_type.id)] += 1

        return {
            "mode": mode,
            "total_count": len(suggestions),
            "changed_count": sum(1 for item in suggestions if item["changed"]),
            "suggestions": suggestions,
            "mapping": mapping,
        }

    @classmethod
    def apply_distribution(
        cls,
        *,
        schedule: MonthlySchedule,
        user,
        mode: str = MODE_BALANCED,
        only_empty: bool = False,
        selected_dates: Optional[Iterable[date]] = None,
        selected_duty_type_ids: Optional[Iterable[int]] = None,
    ) -> dict:
        """
        Применяет результат автораспределения через существующий PlanService.process_post_data(...).
        """
        access = AccessManager(user)
        if not access.can_plan("manage_days", schedule):
            raise PermissionError("Нет прав на автоматическое распределение")

        base_unit = schedule.unit
        allowed_delegate_units = access.allowed_delegate_units_for_plan_days(schedule).exclude(id=base_unit.id)

        dates, duty_types, plans_dict, incoming_days = PlanService.build_table_data(schedule, base_unit)

        preview = cls.preview_distribution(
            schedule=schedule,
            user=user,
            mode=mode,
            only_empty=only_empty,
            selected_dates=selected_dates,
            selected_duty_type_ids=selected_duty_type_ids,
        )

        post_data = QueryDict("", mutable=True)

        for (current_date, duty_type_id), unit_id in preview["mapping"].items():
            post_data[f"day_{current_date.strftime('%Y-%m-%d')}_{duty_type_id}"] = str(unit_id)

        PlanService.process_post_data(
            schedule=schedule,
            post_data=post_data,
            plans_dict=plans_dict,
            incoming_days=incoming_days,
            base_unit=base_unit,
            user=user,
            allowed_delegate_units=allowed_delegate_units,
        )

        return preview

    @classmethod
    def _score_unit(
        cls,
        *,
        mode: str,
        unit: Unit,
        base_unit: Unit,
        capacity: int,
        required_people: int,
        total_month_load: int,
        same_duty_month_load: int,
    ) -> Tuple[int, str]:
        score = 0
        score += total_month_load * cls.BASE_LOAD_WEIGHT
        score += same_duty_month_load * cls.SAME_DUTY_WEIGHT

        if capacity < required_people:
            score += cls.SHORTAGE_PENALTY

        if mode == cls.MODE_PREFER_OWN:
            if unit.id == base_unit.id:
                score -= cls.OWN_UNIT_BONUS
            else:
                score += cls.DELEGATION_PENALTY

        elif mode == cls.MODE_BALANCED:
            if unit.id == base_unit.id:
                score -= 5

        elif mode == cls.MODE_PREFER_CHILDREN:
            if unit.id == base_unit.id:
                score += cls.PREFER_CHILDREN_BASE_PENALTY

        reason = (
            f"score={score}; "
            f"month_load={total_month_load}; "
            f"same_duty_load={same_duty_month_load}; "
            f"capacity={capacity}; "
            f"required={required_people}"
        )
        return score, reason

    @staticmethod
    def _build_unit_month_load(*, year: int, month: int, candidate_units: List[Unit]) -> defaultdict:
        result = defaultdict(int)
        unit_ids = [u.id for u in candidate_units]

        rows = DayPlan.objects.filter(
            schedule__month__year=year,
            schedule__month__month=month,
            unit_id__in=unit_ids,
        ).values_list("unit_id", flat=True)

        for unit_id in rows:
            result[unit_id] += 1

        return result

    @staticmethod
    def _build_unit_duty_month_load(*, year: int, month: int, candidate_units: List[Unit]) -> defaultdict:
        result = defaultdict(int)
        unit_ids = [u.id for u in candidate_units]

        rows = DayPlan.objects.filter(
            schedule__month__year=year,
            schedule__month__month=month,
            unit_id__in=unit_ids,
        ).values_list("unit_id", "duty_type_id")

        for unit_id, duty_type_id in rows:
            result[(unit_id, duty_type_id)] += 1

        return result

    @staticmethod
    def _calculate_capacity(*, unit: Unit, duty_type: DutyType, target_date: date) -> int:
        """
        Сколько людей подразделение реально может выставить на эту дату под этот тип наряда.
        """
        people_qs = (
            Person.objects
            .filter(
                unit=unit,
                clearances__duty_type=duty_type,
            )
            .exclude(
                exemptions__date_from__lte=target_date,
                exemptions__date_to__gte=target_date,
            )
            .distinct()
        )

        # Защита от одновременной занятости в другую смену на эту же дату
        busy_ids = set(
            DutyAssignment.objects.filter(
                day_plan__date=target_date,
                person__unit=unit,
            ).values_list("person_id", flat=True)
        )

        return people_qs.exclude(id__in=busy_ids).count()

    @staticmethod
    def _is_editable_cell(
        *,
        duty_type: DutyType,
        current_date: date,
        existing_plan: Optional[DayPlan],
        incoming_days: set,
        base_unit: Unit,
        allowed_delegate_units: List[Unit],
    ) -> bool:
        """
        Повторяем семантику текущего ручного экрана plans.days:
        - можно работать со своими duty_type базового подразделения;
        - можно работать с принятыми входящими днями;
        - существующие ячейки можно перепривязать между base_unit и разрешёнными delegate units.
        """
        allowed_delegate_ids = {unit.id for unit in allowed_delegate_units}

        if existing_plan is not None:
            return existing_plan.unit_id == base_unit.id or existing_plan.unit_id in allowed_delegate_ids

        if duty_type.created_by_unit_id == base_unit.id:
            return True

        return (current_date, duty_type.id) in incoming_days