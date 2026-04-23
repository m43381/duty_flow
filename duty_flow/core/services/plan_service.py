from __future__ import annotations

import calendar
from collections import Counter
from datetime import datetime
from typing import Dict, Tuple

from django.db import transaction

from duty_plans.models import DayPlan, MonthlySchedule
from duty_types.models import DutyType


class PlanService:
    @staticmethod
    def delete_schedule_with_children(schedule):
        def delete_recursive(sched):
            children = MonthlySchedule.objects.filter(parent_schedule=sched)
            for child in children:
                delete_recursive(child)
            sched.days.all().delete()
            sched.delete()

        delete_recursive(schedule)

    @staticmethod
    def get_month_dates(year, month):
        last_day = calendar.monthrange(year, month)[1]
        return [datetime(year, month, day).date() for day in range(1, last_day + 1)]

    @staticmethod
    def build_table_data(schedule, base_unit):
        year = schedule.month.year
        month = schedule.month.month

        dates = PlanService.get_month_dates(year, month)
        all_plans = schedule.days.select_related("unit", "duty_type").all()

        duty_ids = set()
        for p in all_plans:
            if p.type == "own" or (p.type == "incoming" and p.status == "accepted"):
                duty_ids.add(p.duty_type_id)

        own_duty_types = DutyType.objects.filter(created_by_unit=base_unit)
        for dt in own_duty_types:
            duty_ids.add(dt.id)

        duty_types = DutyType.objects.filter(id__in=duty_ids).order_by("name")

        plans_dict = {}
        for p in all_plans:
            if p.type == "own" or (p.type == "incoming" and p.status == "accepted"):
                plans_dict[(p.date, p.duty_type_id)] = p

        incoming_days = set()
        for p in all_plans:
            if p.type == "incoming" and p.status == "accepted":
                incoming_days.add((p.date, p.duty_type_id))

        return dates, duty_types, plans_dict, incoming_days

    @staticmethod
    def build_table_rows(dates, duty_types, plans_dict, incoming_days, base_unit, allowed_delegate_units):
        allowed_delegate_ids = set(allowed_delegate_units.values_list("id", flat=True))
        table = []

        for duty in duty_types:
            row = {"duty": duty, "cells": []}

            for current_date in dates:
                p = plans_dict.get((current_date, duty.id))
                is_incoming_day = (current_date, duty.id) in incoming_days

                if p:
                    if p.type == "own":
                        if p.child_status == "none":
                            cell_class = "own"
                            status_text = "Своими силами"
                        elif p.child_status == "pending":
                            cell_class = "delegated_pending"
                            status_text = "Делегировано, ждёт"
                        else:
                            cell_class = "delegated_accepted"
                            status_text = "Делегировано, принято"
                    else:
                        if p.status == "accepted":
                            if p.child_status == "pending":
                                cell_class = "incoming_delegated_pending"
                                status_text = "Получен, делегирован, ждёт"
                            elif p.child_status == "accepted":
                                cell_class = "incoming_delegated_accepted"
                                status_text = "Получен, делегирован, принят"
                            else:
                                cell_class = "incoming_active"
                                status_text = "Принят, исполняем"
                        else:
                            cell_class = "incoming_pending"
                            status_text = "Ожидает принятия"

                    can_edit = p.unit_id == base_unit.id or p.unit_id in allowed_delegate_ids
                else:
                    if duty.created_by_unit_id == base_unit.id:
                        can_edit = True
                        cell_class = "empty"
                        status_text = ""
                    elif is_incoming_day:
                        can_edit = True
                        cell_class = "incoming_active"
                        status_text = "Входящий"
                    else:
                        can_edit = False
                        cell_class = "inactive"
                        status_text = ""

                row["cells"].append({
                    "date": current_date,
                    "unit_id": p.unit_id if p else None,
                    "unit_name": p.unit.name if p and p.unit else None,
                    "cell_class": cell_class,
                    "status_text": status_text,
                    "can_edit": can_edit,
                })

            table.append(row)

        return table

    @staticmethod
    def build_distribution_summary_from_table(*, table, base_unit):
        per_unit_counter = Counter()
        per_duty = []
        empty_count = 0
        active_cells = 0

        for row in table:
            duty_counter = Counter()
            duty_total = 0

            for cell in row["cells"]:
                cell_class = cell.get("cell_class")
                unit_name = cell.get("unit_name")
                unit_id = cell.get("unit_id")

                if cell_class == "inactive":
                    continue

                active_cells += 1

                if not unit_id:
                    empty_count += 1
                    continue

                if unit_id == base_unit.id:
                    unit_name = base_unit.name
                elif not unit_name:
                    unit_name = "—"

                per_unit_counter[unit_name] += 1
                duty_counter[unit_name] += 1
                duty_total += 1

            per_duty.append({
                "duty_name": row["duty"].name,
                "total": duty_total,
                "units": [
                    {"unit_name": unit_name, "count": count}
                    for unit_name, count in duty_counter.most_common()
                ],
            })

        unit_rows = [
            {"unit_name": unit_name, "count": count}
            for unit_name, count in per_unit_counter.most_common()
        ]

        allocated_cells = sum(item["count"] for item in unit_rows)

        return {
            "kind": "actual",
            "mode": "actual_table",
            "mode_label": "Текущее состояние таблицы",
            "base_unit_name": base_unit.name,
            "total_cells": active_cells,
            "allocated_cells": allocated_cells,
            "empty_cells": empty_count,
            "unit_rows": unit_rows,
            "duty_rows": per_duty,
        }

    @staticmethod
    def _delete_children_recursive(plan: DayPlan):
        children = list(plan.children.all().select_related("schedule"))
        for child in children:
            PlanService._delete_children_recursive(child)
            child.delete()

    @staticmethod
    def _cleanup_empty_child_schedule(schedule):
        if schedule.parent_schedule_id and not schedule.days.exists():
            schedule.delete()

    @staticmethod
    def _ensure_child_schedule(parent_schedule, month, unit_id, user):
        child_schedule, _ = MonthlySchedule.objects.get_or_create(
            month=month,
            unit_id=unit_id,
            defaults={
                "name": f"Расписание {month.strftime('%B %Y')}",
                "status": "draft",
                "parent_schedule": parent_schedule,
                "created_by": user,
            },
        )
        return child_schedule

    @staticmethod
    def _upsert_root_plan(schedule, target_date, duty_id, unit_id, incoming_days):
        is_incoming = (target_date, duty_id) in incoming_days

        plan, created = DayPlan.objects.get_or_create(
            schedule=schedule,
            date=target_date,
            duty_type_id=duty_id,
            defaults={
                "unit_id": unit_id,
                "type": "incoming" if is_incoming else "own",
                "status": "accepted" if is_incoming else None,
                "child_status": "none",
            },
        )

        if not created:
            plan.unit_id = unit_id
            plan.type = "incoming" if is_incoming else "own"
            plan.status = "accepted" if is_incoming else None
            if not plan.child_status:
                plan.child_status = "none"
            plan.save()

        return plan

    @staticmethod
    def _create_child_plan(parent_plan, child_schedule, unit_id):
        return DayPlan.objects.create(
            schedule=child_schedule,
            date=parent_plan.date,
            duty_type_id=parent_plan.duty_type_id,
            unit_id=unit_id,
            type="incoming",
            status="pending",
            child_status="none",
            parent=parent_plan,
        )

    @staticmethod
    def apply_unit_decisions(
        *,
        schedule,
        decisions: Dict[Tuple[datetime.date, int], int],
        plans_dict,
        incoming_days,
        base_unit,
        user,
        allowed_delegate_units,
    ):
        allowed_delegate_ids = set(allowed_delegate_units.values_list("id", flat=True))
        allowed_unit_ids = {base_unit.id, *allowed_delegate_ids}

        with transaction.atomic():
            for (target_date, duty_id), unit_id in decisions.items():
                if unit_id not in allowed_unit_ids:
                    continue

                root_plan = PlanService._upsert_root_plan(
                    schedule=schedule,
                    target_date=target_date,
                    duty_id=duty_id,
                    unit_id=unit_id,
                    incoming_days=incoming_days,
                )

                old_child_schedules = [child.schedule for child in root_plan.children.all() if child.schedule_id]

                PlanService._delete_children_recursive(root_plan)

                for child_schedule in old_child_schedules:
                    PlanService._cleanup_empty_child_schedule(child_schedule)

                if unit_id == base_unit.id:
                    root_plan.child_status = "none"
                    root_plan.save(update_fields=["child_status"])
                    continue

                root_plan.child_status = "pending"
                root_plan.save(update_fields=["child_status"])

                child_schedule = PlanService._ensure_child_schedule(
                    parent_schedule=schedule,
                    month=schedule.month,
                    unit_id=unit_id,
                    user=user,
                )

                PlanService._create_child_plan(
                    parent_plan=root_plan,
                    child_schedule=child_schedule,
                    unit_id=unit_id,
                )

    @staticmethod
    def process_post_data(schedule, post_data, plans_dict, incoming_days, base_unit, user, allowed_delegate_units):
        allowed_delegate_ids = set(allowed_delegate_units.values_list("id", flat=True))
        allowed_unit_ids = {base_unit.id, *allowed_delegate_ids}

        parsed_data = {}
        editable_keys = set()

        for (target_date, duty_id), plan in plans_dict.items():
            if plan.unit_id == base_unit.id or plan.unit_id in allowed_delegate_ids:
                editable_keys.add((target_date, duty_id))

        for key in incoming_days:
            editable_keys.add(key)

        for key, value in post_data.items():
            if not key.startswith("day_") or not value:
                continue

            parts = key.split("_")
            if len(parts) != 3:
                continue

            date_str = parts[1]
            duty_id = int(parts[2])
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            unit_id = int(value)

            if unit_id not in allowed_unit_ids:
                continue

            parsed_data[(target_date, duty_id)] = unit_id
            editable_keys.add((target_date, duty_id))

        with transaction.atomic():
            if parsed_data:
                PlanService.apply_unit_decisions(
                    schedule=schedule,
                    decisions=parsed_data,
                    plans_dict=plans_dict,
                    incoming_days=incoming_days,
                    base_unit=base_unit,
                    user=user,
                    allowed_delegate_units=allowed_delegate_units,
                )

            keys_to_delete = [key for key in editable_keys if key not in parsed_data]

            for key in keys_to_delete:
                existing = plans_dict.get(key)
                if not existing:
                    continue

                old_child_schedules = [child.schedule for child in existing.children.all() if child.schedule_id]
                PlanService._delete_children_recursive(existing)
                existing.delete()

                for child_schedule in old_child_schedules:
                    PlanService._cleanup_empty_child_schedule(child_schedule)

    @staticmethod
    def accept_incoming_plan(source_plan, user):
        with transaction.atomic():
            source_plan.status = "accepted"
            source_plan.save(update_fields=["status"])

            if source_plan.parent_id:
                parent_plan = source_plan.parent
                parent_plan.child_status = "accepted"
                parent_plan.save(update_fields=["child_status"])

            if source_plan.schedule and source_plan.schedule.status == "draft":
                source_plan.schedule.status = "active"
                source_plan.schedule.save(update_fields=["status"])