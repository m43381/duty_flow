from django import forms

from .models import AccessFieldRule, AccessRule, AccessRuleSet


USER_FIELDS = [
    ("username", "Логин"),
    ("first_name", "Имя"),
    ("last_name", "Фамилия"),
    ("email", "Email"),
    ("unit", "Подразделение"),
]


class RulesetAwareFormMixin:
    def _setup_ruleset_field(self):
        if "ruleset" not in self.fields:
            return

        qs = AccessRuleSet.objects.filter(is_active=True).order_by("-is_default", "name")
        self.fields["ruleset"].queryset = qs

        default_ruleset = AccessRuleSet.get_default()
        if default_ruleset and not self.initial.get("ruleset"):
            self.initial["ruleset"] = default_ruleset.pk

        if qs.count() == 1:
            self.fields["ruleset"].widget = forms.HiddenInput()
            self.fields["ruleset"].required = False


class AccessRuleSetForm(forms.ModelForm):
    class Meta:
        model = AccessRuleSet
        fields = ["name", "code", "description", "is_active", "is_default"]


class AccessRuleForm(RulesetAwareFormMixin, forms.ModelForm):
    class Meta:
        model = AccessRule
        fields = [
            "ruleset",
            "resource",
            "action",
            "subject_level",
            "is_allowed",
            "scope",
            "priority",
            "is_active",
            "note",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_ruleset_field()

        self.fields["resource"].initial = "user"
        self.fields["resource"].disabled = True


class AccessFieldRuleForm(RulesetAwareFormMixin, forms.ModelForm):
    field_name = forms.ChoiceField(label="Поле", choices=USER_FIELDS)

    class Meta:
        model = AccessFieldRule
        fields = [
            "ruleset",
            "resource",
            "action",
            "subject_level",
            "field_name",
            "can_view",
            "can_edit",
            "priority",
            "is_active",
            "note",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_ruleset_field()

        self.fields["resource"].initial = "user"
        self.fields["resource"].disabled = True