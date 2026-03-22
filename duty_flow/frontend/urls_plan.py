from django.urls import path
from . import views_plan

app_name = 'plan'

urlpatterns = [
    # Список расписаний
    path('', views_plan.schedule_list, name='list'),
    
    # Создание расписания
    path('add/', views_plan.schedule_add, name='add'),
    
    # Просмотр/редактирование расписания
    path('<int:pk>/', views_plan.schedule_detail, name='detail'),
    path('<int:pk>/edit/', views_plan.schedule_edit, name='edit'),
    path('<int:pk>/delete/', views_plan.schedule_delete, name='delete'),
    
    # Редактирование дней (таблица)
    path('<int:pk>/days/', views_plan.schedule_days, name='days'),
    
    # Входящие назначения
    path('incoming/', views_plan.incoming_assignments, name='incoming'),
    path('create-from-incoming/<int:day_plan_id>/', views_plan.create_from_incoming, name='create_from_incoming'),
    
    # API для обновления DayPlan
    path('day/<int:day_plan_id>/update/', views_plan.day_update, name='day_update'),
]