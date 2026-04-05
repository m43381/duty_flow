from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Основные разделы
    path('persons/', include('frontend.urls_person')),
    path('plans/', include('frontend.urls_plan')),
    path('types/', include('frontend.urls_type')),
    path('unit-types/', include('frontend.urls_unit_type')),
    path('units/', include('frontend.urls_unit')),
    path('users/', include('frontend.urls_user')),
    path('assignments/', include('frontend.urls_assignment')),  # Добавляем
    
    path('logout/', views.logout_view, name='logout'),
]