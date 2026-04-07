from django.urls import path
from core.views import auth
from django.contrib.auth import views as auth_views

# app_name = 'auth'

urlpatterns = [
    path('', auth.index, name='index'),
    path('dashboard/', auth.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth.logout_view, name='logout'),
]