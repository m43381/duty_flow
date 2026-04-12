"""
Сервис для работы с планами нарядов (расписаниями)
Содержит всю бизнес-логику
"""
from datetime import datetime
import calendar
import logging

from django.db import transaction

from duty_plans.models import MonthlySchedule, DayPlan
from duty_types.models import DutyType

logger = logging.getLogger(__name__)


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

            for date in dates:
                p = plans_dict.get((date, duty.id))
                is_incoming_day = (date, duty.id) in incoming_days

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
                    "date": date,
                    "unit_id": p.unit_id if p else None,
                    "unit_name": p.unit.name if p and p.unit else None,
                    "cell_class": cell_class,
                    "status_text": status_text,
                    "can_edit": can_edit,
                })
            table.append(row)

        return table

    @staticmethod
    def process_post_data(schedule, post_data, plans_dict, incoming_days, base_unit, user, allowed_delegate_units):
        allowed_delegate_ids = set(allowed_delegate_units.values_list("id", flat=True))
        allowed_unit_ids = set(allowed_delegate_ids)
        allowed_unit_ids.add(base_unit.id)

        with transaction.atomic():
            parsed_data = {}
            for key, value in post_data.items():
                if key.startswith("day_") and value:
                    parts = key.split("_")
                    if len(parts) == 3:
                        date_str = parts[1]
                        duty_id = int(parts[2])
                        date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        unit_id = int(value)

                        if unit_id in allowed_unit_ids:
                            parsed_data[(date, duty_id)] = unit_id

            for (date, duty_id), unit_id in parsed_data.items():
                existing = plans_dict.get((date, duty_id))
                is_incoming = (date, duty_id) in incoming_days

                if unit_id == base_unit.id:
                    if existing:
                        if is_incoming:
                            existing.type = "incoming"
                            existing.status = "accepted"
                            existing.child_status = "none"
                        else:
                            existing.type = "own"
                            existing.status = None
                            existing.child_status = "none"
                        existing.unit_id = unit_id
                        existing.save()

                        def delete_children(plan):
                            for child in plan.children.all():
                                delete_children(child)
                                child.delete()

                        delete_children(existing)
                    else:
                        if is_incoming:
                            DayPlan.objects.create(
                                schedule=schedule,
                                date=date,
                                duty_type_id=duty_id,
                                unit_id=unit_id,
                                type="incoming",
                                status="accepted",
                                child_status="none",
                            )
                        else:
                            DayPlan.objects.create(
                                schedule=schedule,
                                date=date,
                                duty_type_id=duty_id,
                                unit_id=unit_id,
                                type="own",
                                status=None,
                                child_status="none",
                            )
                else:
                    if existing:
                        if is_incoming:
                            existing.type = "incoming"
                            existing.status = "accepted"
                            existing.child_status = "pending"
                        else:
                            existing.type = "own"
                            existing.status = None
                            existing.child_status = "pending"
                        existing.unit_id = unit_id
                        existing.save()
                    else:
                        if is_incoming:
                            existing = DayPlan.objects.create(
                                schedule=schedule,
                                date=date,
                                duty_type_id=duty_id,
                                unit_id=unit_id,
                                type="incoming",
                                status="accepted",
                                child_status="pending",
                            )
                        else:
                            existing = DayPlan.objects.create(
                                schedule=schedule,
                                date=date,
                                duty_type_id=duty_id,
                                unit_id=unit_id,
                                type="own",
                                status=None,
                                child_status="pending",
                            )

                    child_schedule, _ = MonthlySchedule.objects.get_or_create(
                        month=schedule.month,
                        unit_id=unit_id,
                        defaults={
                            "name": f"Расписание {schedule.month.strftime('%B %Y')}",
                            "status": "draft",
                            "parent_schedule": schedule,
                            "created_by": user,
                        },
                    )

                    child_plan = existing.children.first()
                    if child_plan:
                        child_plan.schedule = child_schedule
                        child_plan.unit_id = unit_id
                        child_plan.type = "incoming"
                        child_plan.status = "pending"
                        child_plan.child_status = "none"
                        child_plan.parent = existing
                        child_plan.save()
                    else:
                        DayPlan.objects.create(
                            schedule=child_schedule,
                            date=date,
                            duty_type_id=duty_id,
                            unit_id=unit_id,
                            type="incoming",
                            status="pending",
                            child_status="none",
                            parent=existing,
                        )

            keys_to_delete = [key for key in plans_dict.keys() if key not in parsed_data]

            def delete_with_children(plan):
                for child in plan.children.all():
                    delete_with_children(child)
                plan.delete()

            for key in keys_to_delete:
                p = plans_dict.get(key)
                if p:
                    delete_with_children(p)

    @staticmethod
    def accept_incoming_plan(source_plan, user):
        with transaction.atomic():
            schedule, _ = MonthlySchedule.objects.get_or_create(
                month=source_plan.schedule.month,
                unit=user.profile.unit,
                defaults={
                    "name": f"Расписание {source_plan.schedule.month.strftime('%B %Y')}",
                    "status": "draft",
                    "parent_schedule": source_plan.schedule,
                    "created_by": user,
                },
            )

            DayPlan.objects.get_or_create(
                schedule=schedule,
                date=source_plan.date,
                duty_type=source_plan.duty_type,
                defaults={
                    "unit": user.profile.unit,
                    "type": "incoming",
                    "status": "accepted",
                    "child_status": "none",
                    "parent": source_plan,
                },
            )

            source_plan.status = "accepted"
            source_plan.save()

            if source_plan.parent:
                source_plan.parent.child_status = "accepted"
                source_plan.parent.save()

            return schedule