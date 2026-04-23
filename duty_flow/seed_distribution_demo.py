"""
Наполнение БД тестовыми данными для проверки распределения DutyFlow.

Запуск:
    python manage.py shell < seed_distribution_demo.py

или в Django shell:
    exec(open("seed_distribution_demo.py", encoding="utf-8").read())

Что создаёт:
- demo unit types и иерархию подразделений
- demo ranks
- demo users/profiles
- demo people
- demo duty types
- demo clearances и exemptions
- demo monthly schedule

Сценарий данных:
- В режиме balanced_structure все подразделения участвуют.
- В режиме balanced_capacity часть duty types распределяется только туда,
  где реально хватает людей по допускам / exemptions.
"""

from datetime import date, timedelta
from collections import defaultdict

from django.contrib.auth.models import User
from django.db import transaction

from duty_plans.models import MonthlySchedule
from duty_types.models import DutyType
from people.models import Person, DutyClearance, Exemption
from ranks.models import Rank
from units.models import Unit, UnitType
from users_app.models import UserProfile


DEMO_PREFIX = "DEMO"
TARGET_MONTH = date.today().replace(day=1)
RESET_DEMO_DATA = True

ACADEMY_NAME = f"{DEMO_PREFIX} Академия"
FACULTY_1_NAME = f"{DEMO_PREFIX} Ф1"
FACULTY_2_NAME = f"{DEMO_PREFIX} Ф2"

DUTY_SPECS = [
    {
        "name": f"{DEMO_PREFIX} Наряд 1",
        "required_people": 1,
        "clearances": {"A": 6, "F1": 6, "F2": 6},
    },
    {
        "name": f"{DEMO_PREFIX} Наряд 2",
        "required_people": 2,
        "clearances": {"A": 4, "F1": 4, "F2": 4},
    },
    {
        "name": f"{DEMO_PREFIX} Наряд 3",
        "required_people": 1,
        "clearances": {"A": 5, "F1": 2, "F2": 0},
    },
    {
        "name": f"{DEMO_PREFIX} Наряд 4",
        "required_people": 2,
        "clearances": {"A": 2, "F1": 0, "F2": 3},
    },
    {
        "name": f"{DEMO_PREFIX} Наряд 5",
        "required_people": 3,
        "clearances": {"A": 3, "F1": 3, "F2": 3},
    },
]

PEOPLE_PER_UNIT = {
    "A": 8,
    "F1": 7,
    "F2": 7,
}

RANKS = [
    ("Рядовой", 10),
    ("Сержант", 20),
    ("Лейтенант", 30),
]


def log(msg):
    print(f"[seed_distribution_demo] {msg}")


def first_existing_user():
    return User.objects.order_by("id").first()


def ensure_user(username: str, unit: Unit, created_by=None):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "is_staff": True,
            "is_superuser": False,
            "email": f"{username}@example.local",
        },
    )
    if created:
        user.set_password("demo12345")
        user.save(update_fields=["password"])
        log(f"Создан пользователь {username}")

    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={"unit": unit, "created_by": created_by},
    )
    changed = False
    if getattr(profile, "unit_id", None) != unit.id:
        profile.unit = unit
        changed = True
    if changed:
        profile.save()
    return user


@transaction.atomic
def reset_demo_data():
    log("Очистка старых demo-данных...")

    MonthlySchedule.objects.filter(unit__name__startswith=DEMO_PREFIX).delete()
    DutyClearance.objects.filter(duty_type__name__startswith=DEMO_PREFIX).delete()
    Exemption.objects.filter(person__unit__name__startswith=DEMO_PREFIX).delete()
    Person.objects.filter(unit__name__startswith=DEMO_PREFIX).delete()
    DutyType.objects.filter(name__startswith=DEMO_PREFIX).delete()
    UserProfile.objects.filter(user__username__startswith="demo_").delete()
    User.objects.filter(username__startswith="demo_").delete()
    Unit.objects.filter(name__startswith=DEMO_PREFIX).delete()
    UnitType.objects.filter(slug__in=["demo-academy-type", "demo-faculty-type"]).delete()


def get_or_create_demo_unit_type(*, slug: str, name: str, level: int, can_have_children: bool):
    unit_type, _ = UnitType.objects.get_or_create(
        slug=slug,
        defaults={
            "name": name,
            "level": level,
            "can_have_children": can_have_children,
        },
    )

    changed = False
    if unit_type.name != name:
        unit_type.name = name
        changed = True
    if unit_type.level != level:
        unit_type.level = level
        changed = True
    if getattr(unit_type, "can_have_children", None) != can_have_children:
        unit_type.can_have_children = can_have_children
        changed = True

    if changed:
        unit_type.save()

    return unit_type


def get_or_create_demo_unit(*, name: str, unit_type: UnitType, parent: Unit | None):
    unit, _ = Unit.objects.get_or_create(
        name=name,
        defaults={
            "parent": parent,
            "unit_type": unit_type,
        },
    )

    changed = False
    if getattr(unit, "parent_id", None) != (parent.id if parent else None):
        unit.parent = parent
        changed = True
    if getattr(unit, "unit_type_id", None) != unit_type.id:
        unit.unit_type = unit_type
        changed = True

    if changed:
        unit.save()

    return unit


@transaction.atomic
def seed():
    if RESET_DEMO_DATA:
        reset_demo_data()

    creator = first_existing_user()

    academy_type = get_or_create_demo_unit_type(
        slug="demo-academy-type",
        name=f"{DEMO_PREFIX} Академия",
        level=0,
        can_have_children=True,
    )
    faculty_type = get_or_create_demo_unit_type(
        slug="demo-faculty-type",
        name=f"{DEMO_PREFIX} Факультет",
        level=1,
        can_have_children=True,
    )

    academy = get_or_create_demo_unit(
        name=ACADEMY_NAME,
        unit_type=academy_type,
        parent=None,
    )
    faculty_1 = get_or_create_demo_unit(
        name=FACULTY_1_NAME,
        unit_type=faculty_type,
        parent=academy,
    )
    faculty_2 = get_or_create_demo_unit(
        name=FACULTY_2_NAME,
        unit_type=faculty_type,
        parent=academy,
    )

    ensure_user("demo_academy_operator", academy, creator)
    ensure_user("demo_f1_operator", faculty_1, creator)
    ensure_user("demo_f2_operator", faculty_2, creator)

    admin = User.objects.filter(username="admin").first()
    if admin:
        profile, _ = UserProfile.objects.get_or_create(
            user=admin,
            defaults={"unit": academy, "created_by": creator},
        )
        changed = False
        if getattr(profile, "unit_id", None) != academy.id:
            profile.unit = academy
            changed = True
        if changed:
            profile.save()
        log("Профиль admin привязан к DEMO Академия")

    rank_objects = []
    for rank_name, order in RANKS:
        rank, _ = Rank.objects.get_or_create(name=rank_name, defaults={"order": order})
        changed = False
        if getattr(rank, "order", None) != order:
            rank.order = order
            changed = True
        if changed:
            rank.save()
        rank_objects.append(rank)

    units_map = {"A": academy, "F1": faculty_1, "F2": faculty_2}
    people_by_unit = defaultdict(list)

    for unit_code, unit in units_map.items():
        count = PEOPLE_PER_UNIT[unit_code]
        for idx in range(1, count + 1):
            rank = rank_objects[(idx - 1) % len(rank_objects)]
            person, _ = Person.objects.get_or_create(
                unit=unit,
                last_name=f"{unit_code}_Тестов{idx:02d}",
                first_name="Сотрудник",
                middle_name="Демо",
                defaults={"rank": rank},
            )
            changed = False
            if getattr(person, "rank_id", None) != rank.id:
                person.rank = rank
                changed = True
            if changed:
                person.save()
            people_by_unit[unit_code].append(person)

    duty_types = []
    for spec in DUTY_SPECS:
        duty_type, _ = DutyType.objects.get_or_create(
            name=spec["name"],
            defaults={
                "description": "Демо-тип наряда для проверки автоматизации",
                "required_people": spec["required_people"],
                "created_by_unit": academy,
                "unit": None,
            },
        )
        changed = False
        if duty_type.required_people != spec["required_people"]:
            duty_type.required_people = spec["required_people"]
            changed = True
        if getattr(duty_type, "created_by_unit_id", None) != academy.id:
            duty_type.created_by_unit = academy
            changed = True
        if getattr(duty_type, "description", "") != "Демо-тип наряда для проверки автоматизации":
            duty_type.description = "Демо-тип наряда для проверки автоматизации"
            changed = True
        if changed:
            duty_type.save()
        duty_types.append((duty_type, spec))

    for duty_type, spec in duty_types:
        for unit_code, people in people_by_unit.items():
            allowed_count = spec["clearances"].get(unit_code, 0)
            for idx, person in enumerate(people):
                if idx < allowed_count:
                    DutyClearance.objects.get_or_create(person=person, duty_type=duty_type)

    month_start = TARGET_MONTH
    first_span_start = month_start
    first_span_end = month_start + timedelta(days=9)
    mid_span_start = month_start + timedelta(days=10)
    mid_span_end = month_start + timedelta(days=17)

    for person in people_by_unit["F1"][:2]:
        Exemption.objects.get_or_create(
            person=person,
            reason="leave",
            date_from=first_span_start,
            date_to=first_span_end,
            defaults={"comment": "DEMO отпуск для теста автораспределения"},
        )

    for person in people_by_unit["F2"][:1]:
        Exemption.objects.get_or_create(
            person=person,
            reason="trip",
            date_from=mid_span_start,
            date_to=mid_span_end,
            defaults={"comment": "DEMO командировка для теста автораспределения"},
        )

    schedule, created = MonthlySchedule.objects.get_or_create(
        month=TARGET_MONTH,
        unit=academy,
        defaults={
            "name": f"{DEMO_PREFIX} Расписание {TARGET_MONTH.strftime('%m.%Y')}",
            "status": "draft",
            "created_by": creator,
        },
    )
    if not created:
        changed = False
        expected_name = f"{DEMO_PREFIX} Расписание {TARGET_MONTH.strftime('%m.%Y')}"
        if schedule.name != expected_name:
            schedule.name = expected_name
            changed = True
        if getattr(schedule, "status", None) != "draft":
            schedule.status = "draft"
            changed = True
        if creator and getattr(schedule, "created_by_id", None) != creator.id:
            schedule.created_by = creator
            changed = True
        if changed:
            schedule.save()
        log(f"Используется существующее расписание #{schedule.id}")
    else:
        log(f"Создано расписание #{schedule.id}")

    log("")
    log("Готово.")
    log(f"Расписание: id={schedule.id}, unit={academy.name}, month={TARGET_MONTH}")
    log("Типы нарядов:")
    for duty_type, spec in duty_types:
        log(
            f"  - {duty_type.name}: required={duty_type.required_people}; "
            f"A={spec['clearances'].get('A', 0)} F1={spec['clearances'].get('F1', 0)} F2={spec['clearances'].get('F2', 0)}"
        )
    log("")
    log("Как проверять:")
    log("1) Открой расписание DEMO Академии.")
    log("2) Запусти 'Равномерно по структуре' — должны участвовать все подразделения.")
    log("3) Запусти 'Равномерно с учётом людей' — часть типов уйдёт только в те unit, где хватает допуска/ёмкости.")


seed()