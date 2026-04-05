# Схема базы данных

## Таблицы и связи

---

## Unit (Подразделение)

| Поле         | Тип            | Описание                  |
| ------------ | -------------- | ------------------------- |
| id           | PK             | Идентификатор             |
| name         | VARCHAR(255)   | Название подразделения    |
| parent_id    | FK(Unit, NULL) | Вышестоящее подразделение |
| unit_type_id | FK(UnitType)   | Тип подразделения         |

---

## UnitType (Тип подразделения)

| Поле              | Тип         | Описание                                          |
| ----------------- | ----------- | ------------------------------------------------- |
| id                | PK          | Идентификатор                                     |
| name              | VARCHAR(50) | Название типа (например, "Академия", "Факультет") |
| slug              | VARCHAR(50) | Уникальный идентификатор                          |
| level             | SMALLINT    | Уровень иерархии (0 — самый высокий)              |
| can_have_children | BOOLEAN     | Может иметь дочерние подразделения                |

---

## Rank (Звание)

| Поле  | Тип          | Описание               |
| ----- | ------------ | ---------------------- |
| id    | PK           | Идентификатор          |
| name  | VARCHAR(100) | Название звания        |
| order | SMALLINT     | Порядок для сортировки |

---

## Person (Сотрудник)

| Поле        | Тип          | Описание      |
| ----------- | ------------ | ------------- |
| id          | PK           | Идентификатор |
| last_name   | VARCHAR(150) | Фамилия       |
| first_name  | VARCHAR(150) | Имя           |
| middle_name | VARCHAR(150) | Отчество      |
| rank_id     | FK(Rank)     | Звание        |
| unit_id     | FK(Unit)     | Подразделение |

---

## Exemption (Освобождение от нарядов)

| Поле      | Тип         | Описание                                |
| --------- | ----------- | --------------------------------------- |
| id        | PK          | Идентификатор                           |
| person_id | FK(Person)  | Сотрудник                               |
| reason    | VARCHAR(20) | Причина: illness / leave / trip / other |
| date_from | DATE        | Дата начала                             |
| date_to   | DATE        | Дата окончания                          |
| comment   | TEXT        | Комментарий                             |

---

## DutyType (Тип наряда)

| Поле               | Тип            | Описание                        |
| ------------------ | -------------- | ------------------------------- |
| id                 | PK             | Идентификатор                   |
| name               | VARCHAR(150)   | Название наряда                 |
| description        | TEXT           | Описание                        |
| required_people    | SMALLINT       | Требуется человек (default = 1) |
| created_by_unit_id | FK(Unit)       | Подразделение-создатель         |
| unit_id            | FK(Unit, NULL) | Закрепленное подразделение      |
| created_at         | DATETIME       | Дата создания                   |
| updated_at         | DATETIME       | Дата обновления                 |

---

## DutyClearance (Допуск к типу наряда)

| Поле            | Тип                 | Описание        |
| --------------- | ------------------- | --------------- |
| id              | PK                  | Идентификатор   |
| person_id       | FK(Person)          | Сотрудник       |
| duty_type_id    | FK(DutyType)        | Тип наряда      |
| unique_together | (person, duty_type) | Уникальная пара |

---

## MonthlySchedule (Месячное расписание)

| Поле               | Тип                       | Описание                             |
| ------------------ | ------------------------- | ------------------------------------ |
| id                 | PK                        | Идентификатор                        |
| month              | DATE                      | Месяц (первый день месяца)           |
| name               | VARCHAR(255)              | Название расписания                  |
| status             | VARCHAR(20)               | Статус: draft / published / archived |
| unit_id            | FK(Unit)                  | Подразделение                        |
| parent_schedule_id | FK(MonthlySchedule, NULL) | Родительское расписание              |
| created_by_id      | FK(User)                  | Кто создал                           |
| created_at         | DATETIME                  | Дата создания                        |
| updated_at         | DATETIME                  | Дата обновления                      |
| unique_together    | (month, unit)             | Уникальная пара                      |

---

## DayPlan (План на день)

| Поле            | Тип                         | Описание                                   |
| --------------- | --------------------------- | ------------------------------------------ |
| id              | PK                          | Идентификатор                              |
| schedule_id     | FK(MonthlySchedule)         | Расписание                                 |
| date            | DATE                        | Дата                                       |
| duty_type_id    | FK(DutyType)                | Тип наряда                                 |
| unit_id         | FK(Unit, NULL)              | Подразделение-исполнитель                  |
| type            | VARCHAR(20)                 | Тип: own / incoming                        |
| status          | VARCHAR(20)                 | Статус: pending / accepted                 |
| child_status    | VARCHAR(20)                 | Статус дочерних: none / pending / accepted |
| parent_id       | FK(DayPlan, NULL)           | Родительский план                          |
| created_at      | DATETIME                    | Дата создания                              |
| updated_at      | DATETIME                    | Дата обновления                            |
| unique_together | (schedule, date, duty_type) | Уникальная тройка                          |

---

## DutyAssignment (Назначение на наряд)

| Поле            | Тип                | Описание        |
| --------------- | ------------------ | --------------- |
| id              | PK                 | Идентификатор   |
| day_plan_id     | FK(DayPlan)        | План на день    |
| person_id       | FK(Person)         | Сотрудник       |
| assigned_by_id  | FK(User)           | Кто назначил    |
| assigned_at     | DATETIME           | Дата назначения |
| unique_together | (day_plan, person) | Уникальная пара |

---

## User (Пользователь Django)

| Поле        | Тип      | Описание         |
| ----------- | -------- | ---------------- |
| id          | PK       | Идентификатор    |
| username    | VARCHAR  | Логин            |
| password    | VARCHAR  | Пароль           |
| email       | VARCHAR  | Email            |
| first_name  | VARCHAR  | Имя              |
| last_name   | VARCHAR  | Фамилия          |
| is_staff    | BOOLEAN  | Статус персонала |
| is_active   | BOOLEAN  | Активен          |
| date_joined | DATETIME | Дата регистрации |

---

## UserProfile (Профиль пользователя)

| Поле          | Тип            | Описание                |
| ------------- | -------------- | ----------------------- |
| id            | PK             | Идентификатор           |
| user_id       | FK(User)       | Пользователь (OneToOne) |
| unit_id       | FK(Unit)       | Подразделение           |
| created_by_id | FK(User, NULL) | Кто создал              |
| created_at    | DATETIME       | Дата создания           |

---

# Связи (коротко)

```text
UnitType
   └── Unit

Unit
   ├── parent = Unit (самореференс)
   ├── Person
   ├── MonthlySchedule
   ├── DutyType (created_by_unit)
   └── UserProfile

Rank
   └── Person

Person
   ├── Exemption
   ├── DutyClearance
   └── DutyAssignment

DutyType
   ├── DutyClearance
   └── DayPlan

MonthlySchedule
   ├── parent_schedule = MonthlySchedule
   └── DayPlan
          ├── parent = DayPlan
          └── DutyAssignment

User
   ├── UserProfile
   ├── MonthlySchedule (created_by)
   └── DutyAssignment (assigned_by)
```

---

# Иерархия подразделений

## Уровни (UnitType.level)

* 0 — Академия (самый высокий уровень)
* 1 — Факультет
* 2 — Кафедра
* и т.д.

## Правила

* Подразделение может иметь только одного родителя
* Подразделение может иметь множество дочерних
* Тип подразделения определяет:

  * уровень
  * возможность иметь детей

---

# Статусы

## MonthlySchedule.status

```text
draft      — Черновик
published  — Опубликовано
archived   — Архив
```

---

## DayPlan.type

```text
own        — Свой наряд
incoming   — Входящий наряд
```

---

## DayPlan.status

(только для type = incoming)

```text
pending    — Ожидает принятия
accepted   — Принято
```

---

## DayPlan.child_status

```text
none       — Нет дочерних
pending    — Ожидает принятия дочерним
accepted   — Принято дочерним
```

---

## Exemption.reason

```text
illness    — Болезнь
leave      — Отпуск
trip       — Командировка
other      — Другое
```

---

# Примеры запросов

## Получить всех сотрудников подразделения с допусками

```sql
SELECT p.*, dc.duty_type_id
FROM people_person p
LEFT JOIN people_dutyclearance dc
    ON p.id = dc.person_id
WHERE p.unit_id = 1;
```

---

## Получить наряды на сегодня для подразделения

```sql
SELECT dp.*, dt.name
FROM duty_plans_dayplan dp
JOIN duty_types_dutytype dt
    ON dp.duty_type_id = dt.id
WHERE dp.date = CURDATE()
AND dp.unit_id = 1
AND dp.type = 'own';
```

---

## Получить сотрудников, доступных для назначения

```sql
SELECT p.*
FROM people_person p
WHERE p.unit_id = 1

AND EXISTS (
    SELECT 1
    FROM people_dutyclearance dc
    WHERE dc.person_id = p.id
    AND dc.duty_type_id = 1
)

AND NOT EXISTS (
    SELECT 1
    FROM people_exemption e
    WHERE e.person_id = p.id
    AND e.date_from <= CURDATE()
    AND e.date_to >= CURDATE()
);
```

---

## Получить дерево подразделений

```sql
WITH RECURSIVE unit_tree AS (

    SELECT
        id,
        name,
        parent_id,
        0 AS level
    FROM units_unit
    WHERE parent_id IS NULL

    UNION ALL

    SELECT
        u.id,
        u.name,
        u.parent_id,
        ut.level + 1
    FROM units_unit u
    JOIN unit_tree ut
        ON u.parent_id = ut.id

)

SELECT *
FROM unit_tree
ORDER BY level, name;
```
