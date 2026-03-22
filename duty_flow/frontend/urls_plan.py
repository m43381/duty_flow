from django.urls import path
from . import views_plan

app_name = 'plan'

urlpatterns = [
    # Список расписаний (главная страница планов)
    path('', views_plan.schedule_list, name='schedule_list'),
    
    # Создание нового расписания
    path('create/', views_plan.schedule_create, name='schedule_create'),
    
    # Редактирование расписания (карточки дней)
    path('<int:pk>/', views_plan.schedule_edit, name='schedule_edit'),
    
    # Удаление расписания
    path('<int:pk>/delete/', views_plan.schedule_delete, name='schedule_delete'),
]