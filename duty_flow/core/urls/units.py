from django.urls import path
from core.views.units import (
    unit_list, unit_add, unit_detail, unit_edit, unit_delete,
    unit_type_list, unit_type_add, unit_type_detail, 
    unit_type_edit, unit_type_delete
)

# app_name = 'units'

urlpatterns = [
    path('', unit_list, name='list'),
    path('add/', unit_add, name='add'),
    path('<int:pk>/', unit_detail, name='detail'),
    path('<int:pk>/edit/', unit_edit, name='edit'),
    path('<int:pk>/delete/', unit_delete, name='delete'),
]