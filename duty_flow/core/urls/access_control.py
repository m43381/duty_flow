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
    seed_person_rules,
    seed_user_rules,
)

app_name = "access_control"

urlpatterns = [
    path("", access_dashboard, name="dashboard"),

    path("seed-user-rules/", seed_user_rules, name="seed_user_rules"),
    path("seed-person-rules/", seed_person_rules, name="seed_person_rules"),

    path("<str:resource>/matrix/", resource_matrix, name="resource_matrix"),

    path("<str:resource>/rules/", rule_list, name="rules"),
    path("<str:resource>/rules/add/", rule_add, name="rule_add"),
    path("<str:resource>/rules/<int:pk>/edit/", rule_edit, name="rule_edit"),

    path("<str:resource>/field-rules/", field_rule_list, name="field_rules"),
    path("<str:resource>/field-rules/add/", field_rule_add, name="field_rule_add"),
    path("<str:resource>/field-rules/<int:pk>/edit/", field_rule_edit, name="field_rule_edit"),
]