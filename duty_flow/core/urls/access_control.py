from django.urls import path
from core.views import access_control

urlpatterns = [
    path("", access_control.access_dashboard, name="dashboard"),
    path("menu/", access_control.access_menu_matrix, name="menu_matrix"),
    path("diagnostics/", access_control.access_diagnostics, name="diagnostics"),

    path("<str:resource>/seed/", access_control.seed_resource_rules, name="seed_resource_rules"),
    path("<str:resource>/matrix/", access_control.resource_matrix, name="resource_matrix"),

    path("<str:resource>/rules/", access_control.rule_list, name="rules"),
    path("<str:resource>/rules/add/", access_control.rule_add, name="rule_add"),
    path("<str:resource>/rules/<int:pk>/edit/", access_control.rule_edit, name="rule_edit"),

    path("<str:resource>/field-rules/", access_control.field_rule_list, name="field_rules"),
    path("<str:resource>/field-rules/add/", access_control.field_rule_add, name="field_rule_add"),
    path("<str:resource>/field-rules/<int:pk>/edit/", access_control.field_rule_edit, name="field_rule_edit"),
]