from django.urls import path
from frontend.views import person, exemption, clearance

# app_name = 'people'

urlpatterns = [
    path('', person.person_list, name='person_list'),
    path('add/', person.person_add, name='person_add'),
    path('<int:pk>/exemption/add/', exemption.exemption_add, name='exemption_add'),
    path('<int:pk>/exemption/<int:exemption_id>/edit/', exemption.exemption_edit, name='exemption_edit'),
    path('<int:pk>/exemption/<int:exemption_id>/delete/', exemption.exemption_delete, name='exemption_delete'),
    path('<int:pk>/clearance/add/', clearance.clearance_add, name='clearance_add'),
    path('<int:pk>/clearance/<int:clearance_id>/delete/', clearance.clearance_delete, name='clearance_delete'),
    path('<int:pk>/', person.person_detail, name='person_detail'),
    path('<int:pk>/edit/', person.person_edit, name='person_edit'),
    path('<int:pk>/delete/', person.person_delete, name='person_delete'),
]