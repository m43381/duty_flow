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
        "field_actions": [
            ("view", "Просмотр"),
            ("create", "Создание"),
            ("update", "Редактирование"),
        ],
        "choice_actions": [
            ("create", "Создание"),
            ("update", "Редактирование"),
        ],
        "fields": [
            ("username", "Логин"),
            ("first_name", "Имя"),
            ("last_name", "Фамилия"),
            ("email", "Email"),
            ("unit", "Подразделение"),
        ],
        "choice_fields": {
            "create": [("unit", "Подразделение")],
            "update": [("unit", "Подразделение")],
        },
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
        "field_actions": [
            ("view", "Просмотр"),
            ("create", "Создание"),
            ("update", "Редактирование"),
        ],
        "choice_actions": [
            ("create", "Создание"),
            ("update", "Редактирование"),
            ("manage_clearances", "Управление допусками"),
        ],
        "fields": [
            ("last_name", "Фамилия"),
            ("first_name", "Имя"),
            ("middle_name", "Отчество"),
            ("rank", "Звание"),
            ("unit", "Подразделение"),
        ],
        "choice_fields": {
            "create": [("unit", "Подразделение")],
            "update": [("unit", "Подразделение")],
            "manage_clearances": [("duty_type", "Тип наряда")],
        },
    },
    "unit": {
        "title": "Подразделения",
        "actions": [
            ("view", "Просмотр"),
            ("create", "Создание"),
            ("update", "Редактирование"),
            ("delete", "Удаление"),
        ],
        "field_actions": [
            ("view", "Просмотр"),
            ("create", "Создание"),
            ("update", "Редактирование"),
        ],
        "choice_actions": [
            ("create", "Создание"),
            ("update", "Редактирование"),
        ],
        "fields": [
            ("name", "Название"),
            ("parent", "Родительское подразделение"),
            ("unit_type", "Тип подразделения"),
        ],
        "choice_fields": {
            "create": [
                ("parent", "Родительское подразделение"),
                ("unit_type", "Тип подразделения"),
            ],
            "update": [
                ("parent", "Родительское подразделение"),
                ("unit_type", "Тип подразделения"),
            ],
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