from django.core.exceptions import ValidationError
from django.db import models


class AccessRuleSet(models.Model):
    name = models.CharField("Название", max_length=150, unique=True)
    code = models.SlugField("Код", max_length=100, unique=True)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Активен", default=True)
    is_default = models.BooleanField("По умолчанию", default=False)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Набор правил доступа"
        verbose_name_plural = "Наборы правил доступа"
        ordering = ["-is_default", "name"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.is_default:
            qs = AccessRuleSet.objects.filter(is_default=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Только один набор правил может быть набором по умолчанию.")

    @classmethod
    def get_default(cls):
        return (
            cls.objects.filter(is_default=True, is_active=True).first()
            or cls.objects.filter(code="default", is_active=True).first()
        )


class AccessRule(models.Model):
    RESOURCE_CHOICES = [
        ("user", "Пользователи"),
        ("person", "Сотрудники"),
    ]

    ACTION_CHOICES = [
        ("view", "Просмотр"),
        ("create", "Создание"),
        ("update", "Редактирование"),
        ("delete", "Удаление"),
        ("change_password", "Смена пароля"),
        ("manage_exemptions", "Управление освобождениями"),
        ("manage_clearances", "Управление допусками"),
    ]

    SCOPE_CHOICES = [
        ("none", "Ничего"),
        ("own_unit", "Только своё подразделение"),
        ("descendants", "Только дочерние подразделения"),
        ("own_and_descendants", "Своё и дочерние подразделения"),
        ("all", "Все подразделения"),
    ]

    ruleset = models.ForeignKey(
        AccessRuleSet,
        on_delete=models.CASCADE,
        related_name="rules",
        verbose_name="Набор правил",
    )
    resource = models.CharField("Ресурс", max_length=50, choices=RESOURCE_CHOICES)
    action = models.CharField("Действие", max_length=50, choices=ACTION_CHOICES)
    subject_level = models.PositiveSmallIntegerField("Для уровня")
    is_allowed = models.BooleanField("Разрешено", default=True)
    scope = models.CharField("Scope записей", max_length=50, choices=SCOPE_CHOICES, default="none")
    priority = models.PositiveIntegerField("Приоритет", default=100)
    is_active = models.BooleanField("Активно", default=True)
    note = models.CharField("Комментарий", max_length=255, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Правило доступа"
        verbose_name_plural = "Правила доступа"
        ordering = ["resource", "action", "subject_level", "priority", "id"]
        indexes = [
            models.Index(fields=["ruleset", "resource", "action", "subject_level"]),
            models.Index(fields=["is_active", "priority"]),
        ]

    def __str__(self):
        return f"{self.ruleset} | {self.resource}.{self.action} | level={self.subject_level}"


class AccessFieldRule(models.Model):
    RESOURCE_CHOICES = AccessRule.RESOURCE_CHOICES

    ACTION_CHOICES = [
        ("view", "Просмотр"),
        ("create", "Создание"),
        ("update", "Редактирование"),
    ]

    ruleset = models.ForeignKey(
        AccessRuleSet,
        on_delete=models.CASCADE,
        related_name="field_rules",
        verbose_name="Набор правил",
    )
    resource = models.CharField("Ресурс", max_length=50, choices=RESOURCE_CHOICES)
    action = models.CharField("Действие", max_length=50, choices=ACTION_CHOICES)
    subject_level = models.PositiveSmallIntegerField("Для уровня")
    field_name = models.CharField("Поле", max_length=100)
    can_view = models.BooleanField("Можно видеть", default=True)
    can_edit = models.BooleanField("Можно редактировать", default=False)
    priority = models.PositiveIntegerField("Приоритет", default=100)
    is_active = models.BooleanField("Активно", default=True)
    note = models.CharField("Комментарий", max_length=255, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Правило доступа к полю"
        verbose_name_plural = "Правила доступа к полям"
        ordering = ["resource", "action", "field_name", "subject_level", "priority", "id"]
        indexes = [
            models.Index(fields=["ruleset", "resource", "action", "subject_level"]),
            models.Index(fields=["field_name", "is_active"]),
        ]

    def __str__(self):
        return f"{self.ruleset} | {self.resource}.{self.action}.{self.field_name} | level={self.subject_level}"


class AccessChoiceRule(models.Model):
    RESOURCE_CHOICES = AccessRule.RESOURCE_CHOICES
    SCOPE_CHOICES = AccessRule.SCOPE_CHOICES

    ACTION_CHOICES = [
        ("create", "Создание"),
        ("update", "Редактирование"),
    ]

    ruleset = models.ForeignKey(
        AccessRuleSet,
        on_delete=models.CASCADE,
        related_name="choice_rules",
        verbose_name="Набор правил",
    )
    resource = models.CharField("Ресурс", max_length=50, choices=RESOURCE_CHOICES)
    action = models.CharField("Действие", max_length=50, choices=ACTION_CHOICES)
    subject_level = models.PositiveSmallIntegerField("Для уровня")
    field_name = models.CharField("Поле select/queryset", max_length=100)
    scope = models.CharField("Scope значений", max_length=50, choices=SCOPE_CHOICES, default="none")
    is_active = models.BooleanField("Активно", default=True)
    priority = models.PositiveIntegerField("Приоритет", default=100)
    note = models.CharField("Комментарий", max_length=255, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Правило доступа к выпадающему списку"
        verbose_name_plural = "Правила доступа к выпадающим спискам"
        ordering = ["resource", "action", "field_name", "subject_level", "priority", "id"]
        indexes = [
            models.Index(fields=["ruleset", "resource", "action", "field_name", "subject_level"]),
        ]

    def __str__(self):
        return f"{self.ruleset} | {self.resource}.{self.action}.{self.field_name} -> {self.scope}"