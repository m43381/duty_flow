from django.urls import path
from core.views import auth

# app_name = 'auth'

urlpatterns = [
    path('', auth.index, name='index'),
    path('dashboard/', auth.dashboard, name='dashboard'),
    path('logout/', auth.logout_view, name='logout'),
]