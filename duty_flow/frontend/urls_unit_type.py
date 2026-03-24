from django.urls import path
from . import views_unit_type

app_name = 'unit_type'

urlpatterns = [
    path('', views_unit_type.list, name='list'),
    path('add/', views_unit_type.add, name='add'),
    path('<int:pk>/', views_unit_type.detail, name='detail'),
    path('<int:pk>/edit/', views_unit_type.edit, name='edit'),
    path('<int:pk>/delete/', views_unit_type.delete, name='delete'),
]