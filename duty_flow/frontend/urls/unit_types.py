from django.urls import path
from frontend.views.units import (
    unit_type_list, unit_type_add, unit_type_detail, 
    unit_type_edit, unit_type_delete
)

# app_name = 'unit_types'

urlpatterns = [
    path('', unit_type_list, name='list'),
    path('add/', unit_type_add, name='add'),
    path('<int:pk>/', unit_type_detail, name='detail'),
    path('<int:pk>/edit/', unit_type_edit, name='edit'),
    path('<int:pk>/delete/', unit_type_delete, name='delete'),
]