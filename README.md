# Схема базы данных

## Таблицы и связи

### Unit (Подразделение)
| Поле        | Тип                     | Описание                        |
|-------------|-------------------------|---------------------------------|
| id          | PK                      | Идентификатор                  |
| name        | VARCHAR                 | Название подразделения         |
| parent_id   | FK(Unit, NULL)          | Вышестоящее подразделение      |
| unit_type   | ENUM                    | academy/faculty/department/commandant |

### Rank (Звание)
| Поле | Тип   | Описание     |
|------|-------|--------------|
| id   | PK    | Идентификатор|
| name | VARCHAR| Название звания|

### Person (Сотрудник)
| Поле        | Тип          | Описание           |
|-------------|--------------|--------------------|
| id          | PK           | Идентификатор      |
| last_name   | VARCHAR      | Фамилия           |
| first_name  | VARCHAR      | Имя               |
| middle_name | VARCHAR      | Отчество          |
| rank_id     | FK(Rank)     | Звание            |
| unit_id     | FK(Unit)     | Подразделение     |

### Exemption (Освобождение)
| Поле      | Тип             | Описание                  |
|-----------|-----------------|---------------------------|
| id        | PK              | Идентификатор            |
| person_id | FK(Person)      | Сотрудник                |
| reason    | ENUM            | illness/leave/trip/other |
| date_from | DATE            | Дата начала              |
| date_to   | DATE            | Дата окончания           |
| comment   | TEXT, NULL      | Комментарий              |

### DutyType (Тип наряда)
| Поле            | Тип        | Описание                 |
|-----------------|------------|--------------------------|
| id              | PK         | Идентификатор           |
| name            | VARCHAR    | Название наряда         |
| description     | TEXT, NULL | Описание                |
| required_people | INTEGER    | Количество человек (default=1) |

### DutyClearance (Допуск к нарядам)
| Поле         | Тип           | Описание        |
|--------------|---------------|-----------------|
| id           | PK            | Идентификатор   |
| person_id    | FK(Person)    | Сотрудник       |
| duty_type_id | FK(DutyType)  | Тип наряда      |

### DutyPlan (План наряда)
| Поле         | Тип           | Описание        |
|--------------|---------------|-----------------|
| id           | PK            | Идентификатор   |
| date         | DATE          | Дата наряда     |
| unit_id      | FK(Unit)      | Подразделение   |
| duty_type_id | FK(DutyType)  | Тип наряда      |

### DutyAssignment (Назначение на наряд)
| Поле     | Тип          | Описание        |
|----------|--------------|-----------------|
| id       | PK           | Идентификатор   |
| plan_id  | FK(DutyPlan) | План наряда     |
| person_id| FK(Person)   | Сотрудник       |

### DutyLoadStat (Статистика нагрузки)
| Поле        | Тип          | Описание                 |
|-------------|--------------|--------------------------|
| id          | PK           | Идентификатор           |
| person_id   | FK(Person)   | Сотрудник               |
| duty_count  | INTEGER      | Количество назначений   |

## Сервисы

### PlanningEngine
- Автоматическое распределение нарядов
- Учет освобождений
- Учет допусков
- Балансировка нагрузки

## Связи (коротко)

- Unit → parent = Unit (самореференс)
- Person → Rank, Unit
- Exemption → Person
- DutyClearance → Person, DutyType
- DutyPlan → Unit, DutyType
- DutyAssignment → DutyPlan, Person
- DutyLoadStat → Person
