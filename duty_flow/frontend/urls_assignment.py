from django.urls import path
from . import views_assignment

app_name = 'assignment'

urlpatterns = [
    # Основная страница календаря
    path('', views_assignment.calendar, name='calendar'),
    
    # Назначение сотрудника
    path('assign/<int:plan_id>/', views_assignment.assign_person, name='assign'),
    
    # Снятие назначения
    path('unassign/<int:assignment_id>/', views_assignment.unassign_person, name='unassign'),
    
    # Получение доступных сотрудников (AJAX)
    path('get-people/<int:plan_id>/', views_assignment.get_available_people, name='get_people'),
]