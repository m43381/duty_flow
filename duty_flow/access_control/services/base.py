from access_control.models import AccessChoiceRule, AccessFieldRule, AccessRule, AccessRuleSet


class BaseAccessService:
    def __init__(self, ctx):
        self.ctx = ctx
        self.ruleset = self._get_or_create_default_ruleset()

    def _get_or_create_default_ruleset(self):
        ruleset = AccessRuleSet.get_default()
        if ruleset:
            return ruleset

        return AccessRuleSet.objects.create(
            name="Базовый набор",
            code="default",
            description="Основной активный набор правил доступа",
            is_active=True,
            is_default=True,
        )

    def _get_rule(self, resource: str, action: str):
        if self.ruleset is None or self.ctx.user_level is None:
            return None

        return (
            AccessRule.objects.filter(
                ruleset=self.ruleset,
                resource=resource,
                action=action,
                subject_level=self.ctx.user_level,
                is_active=True,
            )
            .order_by("priority", "id")
            .first()
        )

    def _get_field_rules(self, resource: str, action: str):
        if self.ruleset is None or self.ctx.user_level is None:
            return None

        qs = (
            AccessFieldRule.objects.filter(
                ruleset=self.ruleset,
                resource=resource,
                action=action,
                subject_level=self.ctx.user_level,
                is_active=True,
            )
            .order_by("field_name", "priority", "id")
        )

        if not qs.exists():
            return None

        unique_rules = {}
        for item in qs:
            if item.field_name not in unique_rules:
                unique_rules[item.field_name] = item
        return list(unique_rules.values())

    def _get_choice_rule(self, resource: str, action: str, field_name: str):
        if self.ruleset is None or self.ctx.user_level is None:
            return None

        return (
            AccessChoiceRule.objects.filter(
                ruleset=self.ruleset,
                resource=resource,
                action=action,
                field_name=field_name,
                subject_level=self.ctx.user_level,
                is_active=True,
            )
            .order_by("priority", "id")
            .first()
        )