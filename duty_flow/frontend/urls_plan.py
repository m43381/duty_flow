from django.urls import path
from . import views_plan

app_name = 'plan'

urlpatterns = [
    # Базовые CRUD через общий модуль
    path('', views_plan.schedule_list, name='list'),
    path('add/', views_plan.schedule_add, name='add'),
    path('<int:pk>/', views_plan.schedule_detail, name='detail'),
    path('<int:pk>/edit/', views_plan.schedule_edit, name='edit'),
    path('<int:pk>/delete/', views_plan.schedule_delete, name='delete'),
    
    # Редактирование дней в расписании (таблица)
    path('<int:pk>/days/', views_plan.schedule_days, name='days'),
]