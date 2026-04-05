from django.urls import path
from core.views import duty_types

# app_name = 'duty_types'

urlpatterns = [
    path('', duty_types.duty_type_list, name='list'),
    path('add/', duty_types.duty_type_add, name='add'),
    path('<int:pk>/', duty_types.duty_type_detail, name='detail'),
    path('<int:pk>/edit/', duty_types.duty_type_edit, name='edit'),
    path('<int:pk>/delete/', duty_types.duty_type_delete, name='delete'),
]