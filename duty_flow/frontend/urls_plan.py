from django.urls import path
from . import views_plan

app_name = 'plan'

urlpatterns = [
    # Базовый CRUD
    path('', views_plan.plan_list, name='list'),
    path('add/', views_plan.plan_add, name='add'),
    path('<int:pk>/', views_plan.plan_detail, name='detail'),
    path('<int:pk>/edit/', views_plan.plan_edit, name='edit'),
    path('<int:pk>/delete/', views_plan.plan_delete, name='delete'),
    
    # Редактирование дней (таблица)
    path('<int:pk>/days/', views_plan.plan_days, name='days'),
]