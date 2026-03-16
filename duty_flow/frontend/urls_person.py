from django.urls import path
from . import views_person
from . import views_exemption
from . import views_clearance

app_name = 'person'

urlpatterns = [
    # Список сотрудников
    path('', views_person.person_list, name='person_list'),
    
    # Добавление сотрудника
    path('add/', views_person.person_add, name='person_add'),
    
    # Освобождения (самые конкретные)
    path('<int:pk>/exemption/add/', views_exemption.exemption_add, name='exemption_add'),
    path('<int:pk>/exemption/<int:exemption_id>/edit/', views_exemption.exemption_edit, name='exemption_edit'),
    path('<int:pk>/exemption/<int:exemption_id>/delete/', views_exemption.exemption_delete, name='exemption_delete'),
    
    # Допуски
    path('<int:pk>/clearance/add/', views_clearance.clearance_add, name='clearance_add'),
    path('<int:pk>/clearance/<int:clearance_id>/delete/', views_clearance.clearance_delete, name='clearance_delete'),
    
    # Основные операции с сотрудниками (менее конкретные)
    path('<int:pk>/', views_person.person_detail, name='person_detail'),
    path('<int:pk>/edit/', views_person.person_edit, name='person_edit'),
    path('<int:pk>/delete/', views_person.person_delete, name='person_delete'),
]