from django.urls import path
from . import views_plan

app_name = 'plan'

urlpatterns = [
    path('', views_plan.list, name='list'),
    path('add/', views_plan.add, name='add'),
    path('<int:pk>/', views_plan.detail, name='detail'),
    path('<int:pk>/edit/', views_plan.edit, name='edit'),
    path('<int:pk>/delete/', views_plan.delete, name='delete'),
    path('<int:pk>/days/', views_plan.days, name='days'),
    path('incoming/', views_plan.incoming, name='incoming'),
    path('incoming/<int:plan_id>/accept/', views_plan.accept, name='accept'),
]