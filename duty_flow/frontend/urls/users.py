from django.urls import path
from frontend.views import users

# app_name = 'users'

urlpatterns = [
    path('', users.user_list, name='list'),
    path('add/', users.user_create, name='add'),
    path('<int:pk>/', users.user_detail, name='detail'),
    path('<int:pk>/edit/', users.user_edit, name='edit'),
    path('<int:pk>/delete/', users.user_delete, name='delete'),
    path('<int:pk>/change-password/', users.user_change_password, name='change_password'),
]