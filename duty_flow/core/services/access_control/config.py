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
        "choice_fields": [
            ("unit", "Подразделение"),
        ],
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
        ],
        "fields": [
            ("last_name", "Фамилия"),
            ("first_name", "Имя"),
            ("middle_name", "Отчество"),
            ("rank", "Звание"),
            ("unit", "Подразделение"),
        ],
        "choice_fields": [
            ("unit", "Подразделение"),
        ],
    },
}

SCOPES = [
    ("none", "Ничего"),
    ("own_unit", "Только своё подразделение"),
    ("descendants", "Только дочерние подразделения"),
    ("own_and_descendants", "Своё и дочерние подразделения"),
    ("all", "Все подразделения"),
]