from django.urls import path
from frontend.views import duty_types

# app_name = 'duty_types'

urlpatterns = [
    path('', duty_types.list, name='list'),
    path('add/', duty_types.add, name='add'),
    path('<int:pk>/', duty_types.detail, name='detail'),
    path('<int:pk>/edit/', duty_types.edit, name='edit'),
    path('<int:pk>/delete/', duty_types.delete, name='delete'),
]