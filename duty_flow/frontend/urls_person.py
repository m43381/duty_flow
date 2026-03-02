from django.urls import path
from . import views_person

app_name = 'person'

urlpatterns = [
    # Список сотрудников
    path('', views_person.person_list, name='person_list'),
    
    # Добавление сотрудника
    path('add/', views_person.person_add, name='person_add'),
    
    # Просмотр сотрудника
    path('<int:person_id>/', views_person.person_detail, name='person_detail'),
    
    # Редактирование сотрудника
    path('<int:person_id>/edit/', views_person.person_edit, name='person_edit'),
    
    # Удаление сотрудника
    path('<int:person_id>/delete/', views_person.person_delete, name='person_delete'),
]