from django.urls import path
from core.views.people import (
    person_list, person_add, person_detail, person_edit, person_delete,
    exemption_add, exemption_edit, exemption_delete,
    clearance_add, clearance_delete
)

# app_name = 'people'

urlpatterns = [
    path('', person_list, name='person_list'),
    path('add/', person_add, name='person_add'),
    path('<int:pk>/exemption/add/', exemption_add, name='exemption_add'),
    path('<int:pk>/exemption/<int:exemption_id>/edit/', exemption_edit, name='exemption_edit'),
    path('<int:pk>/exemption/<int:exemption_id>/delete/', exemption_delete, name='exemption_delete'),
    path('<int:pk>/clearance/add/', clearance_add, name='clearance_add'),
    path('<int:pk>/clearance/<int:clearance_id>/delete/', clearance_delete, name='clearance_delete'),
    path('<int:pk>/', person_detail, name='person_detail'),
    path('<int:pk>/edit/', person_edit, name='person_edit'),
    path('<int:pk>/delete/', person_delete, name='person_delete'),
]