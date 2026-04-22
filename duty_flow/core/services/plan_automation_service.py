from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, List, Optional, Tuple

from access_control.services import AccessManager
from core.services.plan_service import PlanService
from duty_plans.models import DayPlan, DutyAssignment, MonthlySchedule
from duty_types.models import DutyType
from people.models import Person
from units.models import Unit

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DistributionCandidate:
    unit: Unit
    capacity: Optional[int]
    total_month_load: int
    same_duty_month_load: int
    day_load: int
    day_same_duty_load: int
    rotation_load: int
    score: int
    reason: str


class PlanAutomationService:
    """
    Автоматическое распределение нарядов по подразделениям.

    Режимы:
    - balanced_structure: распределение только по структуре и балансу нагрузки
    - balanced_capacity: распределение с учётом кадровой выполнимости
    - prefer_own: приоритет своему подразделению, с учётом capacity
    - prefer_children: приоритет дочерним подразделениям, с учётом capacity

    Ограничение текущей модели:
    один DayPlan может быть назначен только на одно подразделение.
    """

    MODE_BALANCED = "balanced"  # alias для обратной совместимости
    MODE_BALANCED_STRUCTURE = "balanced_structure"
    MODE_BALANCED_CAPACITY = "balanced_capacity"
    MODE_PREFER_OWN = "prefer_own"
    MODE_PREFER_CHILDREN = "prefer_children"

    BASE_LOAD_WEIGHT = 8
    SAME_DUTY_WEIGHT = 4
    DAY_LOAD_WEIGHT = 20
    DAY_SAME_DUTY_WEIGHT = 12

    DELEGATION_PENALTY = 12
    OWN_UNIT_BONUS = 25
    PREFER_CHILDREN_BASE_PENALTY = 20

    @classmethod
    def normalize_mode(cls, mode: str) -> str:
        if mode == cls.MODE_BALANCED:
            return cls.MODE_BALANCED_CAPACITY
        return mode

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
        mode = cls.normalize_mode(mode)

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
        unit_daily_load = defaultdict(int)
        unit_daily_duty_load = defaultdict(int)

        # Новый счётчик ротации: как часто unit уже выбирался для конкретного duty type
        unit_duty_rotation_load = defaultdict(int)

        suggestions = []
        mapping: Dict[Tuple[date, int], int] = {}
        duty_debug = {}

        for duty_type in duty_types:
            if duty_type.id not in selected_duty_type_ids:
                continue

            duty_eligible = []
            duty_rejected = []

            for unit in candidate_units:
                is_ok, debug_reason, _capacity = cls._is_unit_eligible_for_duty(
                    mode=mode,
                    unit=unit,
                    duty_type=duty_type,
                    dates=dates,
                )
                if is_ok:
                    duty_eligible.append(unit.name)
                else:
                    duty_rejected.append(f"{unit.name}: {debug_reason}")

            duty_debug[duty_type.id] = {
                "duty_name": duty_type.name,
                "eligible_units": duty_eligible,
                "rejected_units": duty_rejected,
            }

            for current_date in dates:
                if current_date not in selected_dates:
                    continue

                existing_plan = plans_dict.get((current_date, duty_type.id))
                if only_empty and existing_plan is not None:
                    continue

                editable = cls._is_editable_cell(
                    duty_type=duty_type,
                    current_date=current_date,
                    existing_plan=existing_plan,
                    incoming_days=incoming_days,
                    base_unit=base_unit,
                    allowed_delegate_units=allowed_delegate_units,
                )
                if not editable:
                    continue

                current_unit_id = existing_plan.unit_id if existing_plan else None
                current_unit_name = existing_plan.unit.name if existing_plan and existing_plan.unit else None

                required_people = duty_type.required_people or 0
                candidates: List[DistributionCandidate] = []

                for unit in candidate_units:
                    is_eligible, reject_reason, capacity = cls._is_unit_eligible_for_date(
                        mode=mode,
                        unit=unit,
                        duty_type=duty_type,
                        target_date=current_date,
                        required_people=required_people,
                    )

                    if not is_eligible:
                        continue

                    total_month_load = unit_month_load[unit.id]
                    same_duty_month_load = unit_duty_month_load[(unit.id, duty_type.id)]
                    day_load = unit_daily_load[(current_date, unit.id)]
                    day_same_duty_load = unit_daily_duty_load[(current_date, unit.id, duty_type.id)]
                    rotation_load = unit_duty_rotation_load[(duty_type.id, unit.id)]

                    score = cls._calculate_score(
                        mode=mode,
                        unit=unit,
                        base_unit=base_unit,
                        total_month_load=total_month_load,
                        same_duty_month_load=same_duty_month_load,
                        day_load=day_load,
                        day_same_duty_load=day_same_duty_load,
                    )

                    reason = (
                        f"score={score}; month={total_month_load}; same_duty={same_duty_month_load}; "
                        f"day={day_load}; day_same_duty={day_same_duty_load}; rotation={rotation_load}; "
                        f"capacity={'n/a' if capacity is None else capacity}; required={required_people}; "
                        f"mode={mode}"
                    )

                    candidates.append(
                        DistributionCandidate(
                            unit=unit,
                            capacity=capacity,
                            total_month_load=total_month_load,
                            same_duty_month_load=same_duty_month_load,
                            day_load=day_load,
                            day_same_duty_load=day_same_duty_load,
                            rotation_load=rotation_load,
                            score=score,
                            reason=reason,
                        )
                    )

                candidates.sort(
                    key=lambda x: (
                        x.score,
                        x.day_load,
                        x.total_month_load,
                        x.same_duty_month_load,
                        x.rotation_load,
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
                        "reason": (
                            "Нет подходящего подразделения"
                            if mode == cls.MODE_BALANCED_STRUCTURE
                            else "Нет подразделения с достаточной кадровой ёмкостью"
                        ),
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
                    "candidates": candidates[:5],
                })

                mapping[(current_date, duty_type.id)] = winner.unit.id

                # динамическая балансировка внутри одного прогона
                unit_month_load[winner.unit.id] += 1
                unit_duty_month_load[(winner.unit.id, duty_type.id)] += 1
                unit_daily_load[(current_date, winner.unit.id)] += 1
                unit_daily_duty_load[(current_date, winner.unit.id, duty_type.id)] += 1
                unit_duty_rotation_load[(duty_type.id, winner.unit.id)] += 1

        summary = cls._build_preview_summary(
            schedule=schedule,
            suggestions=suggestions,
            mode=mode,
            base_unit=base_unit,
        )

        return {
            "mode": mode,
            "total_count": len(suggestions),
            "changed_count": sum(1 for item in suggestions if item["changed"]),
            "suggestions": suggestions,
            "mapping": mapping,
            "duty_debug": duty_debug,
            "summary": summary,
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
        mode = cls.normalize_mode(mode)

        access = AccessManager(user)
        if not access.can_plan("manage_days", schedule):
            raise PermissionError("Нет прав на автоматическое распределение")

        base_unit = schedule.unit
        allowed_delegate_units_qs = access.allowed_delegate_units_for_plan_days(schedule).exclude(
            id=base_unit.id
        )

        dates, duty_types, plans_dict, incoming_days = PlanService.build_table_data(schedule, base_unit)

        preview = cls.preview_distribution(
            schedule=schedule,
            user=user,
            mode=mode,
            only_empty=only_empty,
            selected_dates=selected_dates,
            selected_duty_type_ids=selected_duty_type_ids,
        )

        decisions = {}
        for item in preview["suggestions"]:
            if not item["selected_unit_id"]:
                continue
            if not item["changed"]:
                continue
            decisions[(item["date"], item["duty_type"].id)] = item["selected_unit_id"]

        if decisions:
            PlanService.apply_unit_decisions(
                schedule=schedule,
                decisions=decisions,
                plans_dict=plans_dict,
                incoming_days=incoming_days,
                base_unit=base_unit,
                user=user,
                allowed_delegate_units=allowed_delegate_units_qs,
            )

        return preview

    @classmethod
    def _build_preview_summary(cls, *, schedule, suggestions, mode, base_unit):
        per_unit_counter = Counter()
        per_duty = defaultdict(Counter)
        unresolved_count = 0

        for item in suggestions:
            selected_unit_name = item.get("selected_unit_name")
            if not selected_unit_name:
                unresolved_count += 1
                continue

            per_unit_counter[selected_unit_name] += 1
            per_duty[item["duty_type"].name][selected_unit_name] += 1

        unit_rows = [
            {"unit_name": unit_name, "count": count}
            for unit_name, count in per_unit_counter.most_common()
        ]

        duty_rows = []
        for duty_name in sorted(per_duty.keys()):
            unit_distribution = [
                {"unit_name": unit_name, "count": count}
                for unit_name, count in per_duty[duty_name].most_common()
            ]
            duty_rows.append({
                "duty_name": duty_name,
                "total": sum(per_duty[duty_name].values()),
                "units": unit_distribution,
            })

        return {
            "mode": mode,
            "base_unit_name": base_unit.name,
            "total_cells": len(suggestions),
            "changed_cells": sum(1 for item in suggestions if item["changed"]),
            "unresolved_cells": unresolved_count,
            "unit_rows": unit_rows,
            "duty_rows": duty_rows,
        }

    @classmethod
    def _is_unit_eligible_for_duty(
        cls,
        *,
        mode: str,
        unit: Unit,
        duty_type: DutyType,
        dates: List[date],
    ) -> Tuple[bool, str, Optional[int]]:
        if mode == cls.MODE_BALANCED_STRUCTURE:
            return True, "структурный режим", None

        max_capacity = 0
        for target_date in dates:
            capacity = cls._calculate_capacity(unit=unit, duty_type=duty_type, target_date=target_date)
            max_capacity = max(max_capacity, capacity)

        if max_capacity <= 0:
            return False, "нет сотрудников с допуском / все недоступны", 0

        required_people = duty_type.required_people or 0
        if required_people and max_capacity < required_people:
            return False, f"max capacity {max_capacity} < required {required_people}", max_capacity

        return True, "достаточная кадровая ёмкость", max_capacity

    @classmethod
    def _is_unit_eligible_for_date(
        cls,
        *,
        mode: str,
        unit: Unit,
        duty_type: DutyType,
        target_date: date,
        required_people: int,
    ) -> Tuple[bool, str, Optional[int]]:
        if mode == cls.MODE_BALANCED_STRUCTURE:
            return True, "структурный режим", None

        capacity = cls._calculate_capacity(
            unit=unit,
            duty_type=duty_type,
            target_date=target_date,
        )

        if capacity <= 0:
            return False, "capacity=0", capacity

        if required_people and capacity < required_people:
            return False, f"capacity {capacity} < required {required_people}", capacity

        return True, "ok", capacity

    @classmethod
    def _calculate_score(
        cls,
        *,
        mode: str,
        unit: Unit,
        base_unit: Unit,
        total_month_load: int,
        same_duty_month_load: int,
        day_load: int,
        day_same_duty_load: int,
    ) -> int:
        score = 0
        score += total_month_load * cls.BASE_LOAD_WEIGHT
        score += same_duty_month_load * cls.SAME_DUTY_WEIGHT
        score += day_load * cls.DAY_LOAD_WEIGHT
        score += day_same_duty_load * cls.DAY_SAME_DUTY_WEIGHT

        if mode == cls.MODE_PREFER_OWN:
            if unit.id == base_unit.id:
                score -= cls.OWN_UNIT_BONUS
            else:
                score += cls.DELEGATION_PENALTY

        elif mode == cls.MODE_PREFER_CHILDREN:
            if unit.id == base_unit.id:
                score += cls.PREFER_CHILDREN_BASE_PENALTY

        return score

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
        available_people = (
            Person.objects
            .filter(unit=unit, clearances__duty_type=duty_type)
            .exclude(
                exemptions__date_from__lte=target_date,
                exemptions__date_to__gte=target_date,
            )
            .distinct()
        )

        busy_ids = set(
            DutyAssignment.objects.filter(
                day_plan__date=target_date,
                person__unit=unit,
            ).values_list("person_id", flat=True)
        )

        return available_people.exclude(id__in=busy_ids).count()

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
        allowed_delegate_ids = {unit.id for unit in allowed_delegate_units}

        if existing_plan is not None:
            return existing_plan.unit_id == base_unit.id or existing_plan.unit_id in allowed_delegate_ids

        if duty_type.created_by_unit_id == base_unit.id:
            return True

        return (current_date, duty_type.id) in incoming_days