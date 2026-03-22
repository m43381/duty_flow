from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Основные разделы
    path('persons/', include('frontend.urls_person')),
    path('plans/', include('frontend.urls_plan')),
    path('types/', include('frontend.urls_type')),
    path('units/', views.unit_list, name='unit_list'),
    path('users/', views.user_list, name='user_list'),
    
    # Кабинеты (опционально)
    path('cabinet/commandant/', views.commandant_cabinet, name='commandant_cabinet'),
    path('cabinet/faculty/', views.faculty_cabinet, name='faculty_cabinet'),
    path('cabinet/department/', views.department_cabinet, name='department_cabinet'),
    path('logout/', views.logout_view, name='logout'),
]