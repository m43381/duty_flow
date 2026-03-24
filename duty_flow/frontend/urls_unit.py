from django.urls import path
from . import views_unit

app_name = 'units'

urlpatterns = [
    path('', views_unit.list, name='list'),
    path('add/', views_unit.add, name='add'),
    path('<int:pk>/', views_unit.detail, name='detail'),
    path('<int:pk>/edit/', views_unit.edit, name='edit'),
    path('<int:pk>/delete/', views_unit.delete, name='delete'),
]