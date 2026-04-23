from django.urls import path
from core.views import assignments

urlpatterns = [
    path("", assignments.calendar, name="calendar"),
    path("assign/<int:plan_id>/", assignments.assign_person, name="assign"),
    path("unassign/<int:assignment_id>/", assignments.unassign_person, name="unassign"),
    path("get-people/<int:plan_id>/", assignments.get_available_people, name="get_people"),

    path("preview-auto/", assignments.preview_auto_assign, name="preview_auto"),
    path("apply-auto/", assignments.apply_auto_assign, name="apply_auto"),
    path("clear-auto-preview/", assignments.clear_auto_assign_preview, name="clear_auto_preview"),
]