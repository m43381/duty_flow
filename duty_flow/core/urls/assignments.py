from django.urls import path
from core.views import assignments

# app_name = 'assignments'

urlpatterns = [
    path('', assignments.calendar, name='calendar'),
    path('assign/<int:plan_id>/', assignments.assign_person, name='assign'),
    path('unassign/<int:assignment_id>/', assignments.unassign_person, name='unassign'),
    path('get-people/<int:plan_id>/', assignments.get_available_people, name='get_people'),
]