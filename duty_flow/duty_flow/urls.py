from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core.views import auth as frontend_auth

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('', include('core.urls')),
]