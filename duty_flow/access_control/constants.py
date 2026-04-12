SUBJECT_TYPE_LEVEL = "level"

SUBJECT_TYPE_CHOICES = [
    (SUBJECT_TYPE_LEVEL, "Уровень доступа"),
]

RESOURCE_USER = "user"

RESOURCE_CHOICES = [
    (RESOURCE_USER, "Пользователи"),
]

ACTION_VIEW = "view"
ACTION_CREATE = "create"
ACTION_UPDATE = "update"
ACTION_DELETE = "delete"
ACTION_CHANGE_PASSWORD = "change_password"

ACTION_CHOICES = [
    (ACTION_VIEW, "Просмотр"),
    (ACTION_CREATE, "Создание"),
    (ACTION_UPDATE, "Редактирование"),
    (ACTION_DELETE, "Удаление"),
    (ACTION_CHANGE_PASSWORD, "Смена пароля"),
]

SCOPE_NONE = "none"
SCOPE_OWN_UNIT = "own_unit"
SCOPE_DESCENDANTS = "descendants"
SCOPE_OWN_AND_DESCENDANTS = "own_and_descendants"
SCOPE_ALL = "all"

SCOPE_CHOICES = [
    (SCOPE_NONE, "Ничего"),
    (SCOPE_OWN_UNIT, "Только своё подразделение"),
    (SCOPE_DESCENDANTS, "Только дочерние подразделения"),
    (SCOPE_OWN_AND_DESCENDANTS, "Своё и дочерние подразделения"),
    (SCOPE_ALL, "Все подразделения"),
]

DEFAULT_RULESET_CODE = "default"

RESOURCE_ACTIONS = {
    RESOURCE_USER: {
        ACTION_VIEW,
        ACTION_CREATE,
        ACTION_UPDATE,
        ACTION_DELETE,
        ACTION_CHANGE_PASSWORD,
    },
}