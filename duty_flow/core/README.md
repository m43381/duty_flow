# Core — основное приложение

## Описание

**Core** содержит всю бизнес-логику, маршруты, представления и сервисы проекта.

---

## Структура

```text
core/
├── urls/                  # URL-конфигурация
│   ├── __init__.py        # Главный URLconf
│   ├── auth.py            # Аутентификация
│   ├── people.py          # Сотрудники
│   ├── plans.py           # Расписания
│   ├── duty_types.py      # Типы нарядов
│   ├── units.py           # Подразделения
│   ├── unit_types.py      # Типы подразделений
│   ├── users.py           # Пользователи
│   └── assignments.py     # Назначения
│
├── views/                 # Представления
│   ├── auth.py
│   ├── people/
│   │   ├── person.py
│   │   ├── exemption.py
│   │   └── clearance.py
│   ├── units/
│   │   ├── unit.py
│   │   └── unit_type.py
│   └── assignments.py
│
├── services/              # Бизнес-логика
│   ├── plan_service.py
│   ├── people_service.py
│   ├── unit_service.py
│   ├── user_service.py
│   └── assignment_service.py
│
├── templatetags/          # Фильтры шаблонов
│   └── custom_filters.py
│
├── templates/             # HTML-шаблоны
└── static/                # CSS, JS файлы
```

---

# Принципы архитектуры

## Разделение ответственности

* **URLs** — только маршрутизация
* **Views** — только:

  * обработка GET/POST
  * вызов сервисов
  * рендер шаблонов
* **Services** — вся бизнес-логика

---

## Пространства имён в URLs

```text
auth:index
auth:dashboard
auth:logout

people:person_list
people:person_detail

plan:list
plan:days

units:list
units:detail

users:list
users:detail

assignment:calendar
```

---

## Использование в шаблонах

```django
{% url 'auth:dashboard' %}
{% url 'people:person_list' %}
{% url 'plan:list' %}
```

---

# Сервисы

## PlanService

| Метод                                                                             | Описание                        |
| --------------------------------------------------------------------------------- | ------------------------------- |
| delete_schedule_with_children(schedule)                                           | Рекурсивное удаление расписания |
| get_month_dates(year, month)                                                      | Список дат месяца               |
| build_table_data(schedule, user_unit)                                             | Данные для таблицы нарядов      |
| build_table_rows(dates, duty_types, plans_dict, incoming_day, user_unit)          | Построение таблицы              |
| process_post_data(schedule, post_data, plans_dict, incoming_day, user_unit, user) | Обработка делегирования         |
| accept_incoming_plan(source_plan, user)                                           | Принятие входящего наряда       |

---

## PeopleService

| Метод                                                           | Описание                          |
| --------------------------------------------------------------- | --------------------------------- |
| check_exemption_overlap(person, date_from, date_to, exclude_id) | Проверка пересечения освобождений |
| create_exemption(person, form_data)                             | Создание освобождения             |
| update_exemption(exemption, form_data)                          | Обновление освобождения           |
| delete_exemption(exemption)                                     | Удаление освобождения             |
| create_clearance(person, duty_type)                             | Создание допуска                  |
| delete_clearance(clearance)                                     | Удаление допуска                  |

---

## UnitService

| Метод                                                              | Описание                        |
| ------------------------------------------------------------------ | ------------------------------- |
| build_unit_tree(units_qs, root_units, editable_ids, deletable_ids) | Построение дерева подразделений |
| can_delete_unit(unit, user)                                        | Проверка возможности удаления   |
| get_root_units(units_qs, user_level, user_unit)                    | Определение корневых узлов      |

---

## UserService

| Метод                                | Описание                   |
| ------------------------------------ | -------------------------- |
| get_visible_users(user)              | Пользователи с учётом прав |
| search_users(users_qs, search_query) | Поиск пользователей        |
| create_user(form_data, created_by)   | Создание пользователя      |
| update_user(user, form_data)         | Обновление пользователя    |
| change_password(user, new_password)  | Смена пароля               |

---

## AssignmentService

| Метод                                                  | Описание                        |
| ------------------------------------------------------ | ------------------------------- |
| build_calendar_data(day_plans, year, month, user_unit) | Построение календаря назначений |
| get_available_people_for_plan(plan, user_unit)         | Доступные сотрудники для наряда |
| can_assign_to_plan(plan, user_unit, person)            | Проверка возможности назначения |
| can_edit_plan(plan, user_unit)                         | Проверка прав на редактирование |

---

# Кастомные фильтры

`templatetags/custom_filters.py`

## repeat

Повторяет строку указанное количество раз.

```django
{{ '—'|repeat:level }}
```

---

## get_item

Получает значение из словаря по ключу.

```django
{{ dictionary|get_item:key }}
```

---

# Шаблоны

## Основные

```text
base.html
index.html
registration/login.html
```

---

## Разделы

| Папка        | Содержание                             |
| ------------ | -------------------------------------- |
| cabins/      | Личные кабинеты, дашборд               |
| people/      | Список, детали, формы сотрудников      |
| plan/        | Расписания, таблица нарядов, входящие  |
| units/       | Дерево подразделений                   |
| unit_type/   | Типы подразделений                     |
| type/        | Типы нарядов                           |
| users/       | Управление пользователями              |
| assignments/ | Календарь назначений                   |
| components/  | Навигация, переиспользуемые компоненты |

---

# Маршруты

## Auth (`auth:`)

| Имя       | URL         | Описание          |
| --------- | ----------- | ----------------- |
| index     | /           | Главная страница  |
| dashboard | /dashboard/ | Панель управления |
| logout    | /logout/    | Выход             |

---

## People (`people:`)

| Имя              | URL                                                                      | Описание                   |
| ---------------- | ------------------------------------------------------------------------ | -------------------------- |
| person_list      | /                                                                        | Список сотрудников         |
| person_add       | /add/                                                                    | Добавление                 |
| person_detail    | /[int:pk](int:pk)/                                                       | Просмотр                   |
| person_edit      | /[int:pk](int:pk)/edit/                                                  | Редактирование             |
| person_delete    | /[int:pk](int:pk)/delete/                                                | Удаление                   |
| exemption_add    | /[int:pk](int:pk)/exemption/add/                                         | Добавить освобождение      |
| exemption_edit   | /[int:pk](int:pk)/exemption/[int:exemption_id](int:exemption_id)/edit/   | Редактировать освобождение |
| exemption_delete | /[int:pk](int:pk)/exemption/[int:exemption_id](int:exemption_id)/delete/ | Удалить освобождение       |
| clearance_add    | /[int:pk](int:pk)/clearance/add/                                         | Добавить допуск            |
| clearance_delete | /[int:pk](int:pk)/clearance/[int:clearance_id](int:clearance_id)/delete/ | Удалить допуск             |

---

## Plans (`plan:`)

| Имя      | URL                                          | Описание          |
| -------- | -------------------------------------------- | ----------------- |
| list     | /                                            | Список расписаний |
| add      | /add/                                        | Создание          |
| detail   | /[int:pk](int:pk)/                           | Просмотр          |
| edit     | /[int:pk](int:pk)/edit/                      | Редактирование    |
| delete   | /[int:pk](int:pk)/delete/                    | Удаление          |
| days     | /[int:pk](int:pk)/days/                      | Таблица нарядов   |
| incoming | /incoming/                                   | Входящие наряды   |
| accept   | /incoming/[int:plan_id](int:plan_id)/accept/ | Принять входящий  |

---

## Units (`units:`)

| Имя    | URL                       | Описание        |
| ------ | ------------------------- | --------------- |
| list   | /                         | Список (дерево) |
| add    | /add/                     | Создание        |
| detail | /[int:pk](int:pk)/        | Просмотр        |
| edit   | /[int:pk](int:pk)/edit/   | Редактирование  |
| delete | /[int:pk](int:pk)/delete/ | Удаление        |

---

## Users (`users:`)

| Имя             | URL                                | Описание       |
| --------------- | ---------------------------------- | -------------- |
| list            | /                                  | Список         |
| add             | /add/                              | Создание       |
| detail          | /[int:pk](int:pk)/                 | Просмотр       |
| edit            | /[int:pk](int:pk)/edit/            | Редактирование |
| delete          | /[int:pk](int:pk)/delete/          | Удаление       |
| change_password | /[int:pk](int:pk)/change-password/ | Смена пароля   |

---

## Assignments (`assignment:`)

| Имя        | URL                                               | Описание                   |
| ---------- | ------------------------------------------------- | -------------------------- |
| calendar   | /                                                 | Календарь назначений       |
| assign     | /assign/[int:plan_id](int:plan_id)/               | Назначить сотрудника       |
| unassign   | /unassign/[int:assignment_id](int:assignment_id)/ | Снять назначение           |
| get_people | /get-people/[int:plan_id](int:plan_id)/           | AJAX: доступные сотрудники |

---

# Разработка

## Добавление нового функционала

1. Создать метод в соответствующем сервисе
2. Создать view, который вызывает этот метод
3. Добавить маршрут в соответствующий `urls/*.py`
4. Обновить навигацию:

```text
templates/components/navigation.html
```

---

# Правила именования

## Пространства имён

```text
people
units
users
```

(множественное число)

---

## Имена функций

```text
person_list
person_add
person_detail
```

---

## URL-паттерны

```text
/<int:pk>/edit/
/<int:pk>/delete/
```
