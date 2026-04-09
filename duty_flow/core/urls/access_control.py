from django.urls import path

from core.views.access_control import (
    access_dashboard,
    field_rule_add,
    field_rule_edit,
    field_rule_list,
    resource_matrix,
    rule_add,
    rule_edit,
    rule_list,
    seed_resource_rules,
)

app_name = "access_control"

urlpatterns = [
    path("", access_dashboard, name="dashboard"),

    path("<str:resource>/seed/", seed_resource_rules, name="seed_resource_rules"),
    path("<str:resource>/matrix/", resource_matrix, name="resource_matrix"),

    path("<str:resource>/rules/", rule_list, name="rules"),
    path("<str:resource>/rules/add/", rule_add, name="rule_add"),
    path("<str:resource>/rules/<int:pk>/edit/", rule_edit, name="rule_edit"),

    path("<str:resource>/field-rules/", field_rule_list, name="field_rules"),
    path("<str:resource>/field-rules/add/", field_rule_add, name="field_rule_add"),
    path("<str:resource>/field-rules/<int:pk>/edit/", field_rule_edit, name="field_rule_edit"),
]