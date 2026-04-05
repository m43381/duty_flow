from django.urls import path
from frontend.views import users

# app_name = 'users'

urlpatterns = [
    path('', users.list_view, name='list'),
    path('add/', users.create_view, name='add'),
    path('<int:pk>/', users.detail_view, name='detail'),
    path('<int:pk>/edit/', users.edit_view, name='edit'),
    path('<int:pk>/delete/', users.delete_view, name='delete'),
    path('<int:pk>/change-password/', users.change_password_view, name='change_password'),
]