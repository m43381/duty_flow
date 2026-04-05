from django.urls import path
from frontend.views import unit_types

# app_name = 'unit_types'

urlpatterns = [
    path('', unit_types.list, name='list'),
    path('add/', unit_types.add, name='add'),
    path('<int:pk>/', unit_types.detail, name='detail'),
    path('<int:pk>/edit/', unit_types.edit, name='edit'),
    path('<int:pk>/delete/', unit_types.delete, name='delete'),
]