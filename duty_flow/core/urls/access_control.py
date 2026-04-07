from django.urls import path

from core.views.access_control import (
    access_dashboard,
    field_rule_add,
    field_rule_edit,
    field_rule_list,
    rule_add,
    rule_edit,
    rule_list,
    seed_user_rules,
)

app_name = "access_control"

urlpatterns = [
    path("", access_dashboard, name="dashboard"),
    path("seed-user-rules/", seed_user_rules, name="seed_user_rules"),

    path("rules/", rule_list, name="rules"),
    path("rules/add/", rule_add, name="rule_add"),
    path("rules/<int:pk>/edit/", rule_edit, name="rule_edit"),

    path("field-rules/", field_rule_list, name="field_rules"),
    path("field-rules/add/", field_rule_add, name="field_rule_add"),
    path("field-rules/<int:pk>/edit/", field_rule_edit, name="field_rule_edit"),
]