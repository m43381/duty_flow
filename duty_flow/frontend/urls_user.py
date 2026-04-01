from django.urls import path
from . import views_user

app_name = 'users'

urlpatterns = [
    path('', views_user.list_view, name='list'),
    path('add/', views_user.create_view, name='add'),
    path('<int:pk>/', views_user.detail_view, name='detail'),
    path('<int:pk>/edit/', views_user.edit_view, name='edit'),
    path('<int:pk>/delete/', views_user.delete_view, name='delete'),
    path('<int:pk>/change-password/', views_user.change_password_view, name='change_password'),
]