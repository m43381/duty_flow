from django.urls import path
from . import views_type

app_name = 'type'

urlpatterns = [
    path('', views_type.list, name='list'),
    path('add/', views_type.add, name='add'),
    path('<int:pk>/', views_type.detail, name='detail'),
    path('<int:pk>/edit/', views_type.edit, name='edit'),
    path('<int:pk>/delete/', views_type.delete, name='delete'),
]