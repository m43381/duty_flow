RESOURCE_CONFIG = {
    "user": {
        "title": "Пользователи",
        "actions": [
            ("view", "Просмотр"),
            ("create", "Создание"),
            ("update", "Редактирование"),
            ("delete", "Удаление"),
            ("change_password", "Смена пароля"),
        ],
        "field_actions": [("view", "Просмотр"), ("create", "Создание"), ("update", "Редактирование")],
        "choice_actions": [("create", "Создание"), ("update", "Редактирование")],
        "fields": [("username", "Логин"), ("first_name", "Имя"), ("last_name", "Фамилия"), ("email", "Email"), ("unit", "Подразделение")],
        "choice_fields": {"create": [("unit", "Подразделение")], "update": [("unit", "Подразделение")]},
    },
    "person": {
        "title": "Сотрудники",
        "actions": [
            ("view", "Просмотр"),
            ("create", "Создание"),
            ("update", "Редактирование"),
            ("delete", "Удаление"),
            ("manage_exemptions", "Управление освобождениями"),
            ("manage_clearances", "Управление допусками"),
        ],
        "field_actions": [("view", "Просмотр"), ("create", "Создание"), ("update", "Редактирование")],
        "choice_actions": [("create", "Создание"), ("update", "Редактирование"), ("manage_clearances", "Управление допусками")],
        "fields": [("last_name", "Фамилия"), ("first_name", "Имя"), ("middle_name", "Отчество"), ("rank", "Звание"), ("unit", "Подразделение")],
        "choice_fields": {
            "create": [("unit", "Подразделение")],
            "update": [("unit", "Подразделение")],
            "manage_clearances": [("duty_type", "Тип наряда")],
        },
    },
    "unit": {
        "title": "Подразделения",
        "actions": [("view", "Просмотр"), ("create", "Создание"), ("update", "Редактирование"), ("delete", "Удаление")],
        "field_actions": [("view", "Просмотр"), ("create", "Создание"), ("update", "Редактирование")],
        "choice_actions": [("create", "Создание"), ("update", "Редактирование")],
        "fields": [("name", "Название"), ("parent", "Родительское подразделение"), ("unit_type", "Тип подразделения")],
        "choice_fields": {
            "create": [("parent", "Родительское подразделение"), ("unit_type", "Тип подразделения")],
            "update": [("parent", "Родительское подразделение"), ("unit_type", "Тип подразделения")],
        },
    },
    "unit_type": {
        "title": "Типы подразделений",
        "actions": [("view", "Просмотр"), ("create", "Создание"), ("update", "Редактирование"), ("delete", "Удаление")],
        "field_actions": [("view", "Просмотр"), ("create", "Создание"), ("update", "Редактирование")],
        "choice_actions": [],
        "fields": [("name", "Название"), ("level", "Уровень")],
        "choice_fields": {},
    },
    "duty_type": {
        "title": "Типы нарядов",
        "actions": [("view", "Просмотр"), ("create", "Создание"), ("update", "Редактирование"), ("delete", "Удаление")],
        "field_actions": [("view", "Просмотр"), ("create", "Создание"), ("update", "Редактирование")],
        "choice_actions": [("create", "Создание"), ("update", "Редактирование")],
        "fields": [("name", "Название"), ("description", "Описание"), ("required_people", "Требуется человек"), ("unit", "Подразделение")],
        "choice_fields": {"create": [("unit", "Подразделение")], "update": [("unit", "Подразделение")]},
    },
    "plan": {
        "title": "Планы нарядов",
        "actions": [
            ("view", "Просмотр расписаний"),
            ("create", "Создание расписаний"),
            ("update", "Редактирование реквизитов"),
            ("delete", "Удаление расписаний"),
            ("manage_days", "Таблица дней и делегирование"),
            ("accept_incoming", "Входящие и принятие"),
        ],
        "field_actions": [("view", "Просмотр"), ("create", "Создание"), ("update", "Редактирование")],
        "choice_actions": [("manage_days", "Таблица дней и делегирование")],
        "fields": [("month", "Месяц"), ("name", "Название"), ("status", "Статус")],
        "choice_fields": {
            "manage_days": [("delegate_unit", "Подразделения для делегирования")],
        },
    },
}

SCOPES = [
    ("none", "Ничего"),
    ("own_unit", "Только своё подразделение"),
    ("descendants", "Только дочерние подразделения"),
    ("own_and_descendants", "Своё и дочерние подразделения"),
    ("all", "Все подразделения"),
]

CHOICE_MODES = [
    ("scope", "По scope"),
    ("specific_units", "Только конкретные подразделения"),
    ("scope_plus_units", "Scope + конкретные подразделения"),
    ("all_values", "Все значения"),
    ("specific_unit_types", "Только конкретные типы подразделений"),
]