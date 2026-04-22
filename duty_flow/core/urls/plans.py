from django.urls import path
from core.views import plans

# app_name = 'plans'

urlpatterns = [
    path("", plans.list, name="list"),
    path('add/', plans.add, name='add'),
    path('<int:pk>/', plans.detail, name='detail'),
    path('<int:pk>/edit/', plans.edit, name='edit'),
    path('<int:pk>/delete/', plans.delete, name='delete'),
    path('<int:pk>/days/', plans.days, name='days'),
    path('incoming/', plans.incoming, name='incoming'),
    path('incoming/<int:plan_id>/accept/', plans.accept, name='accept'),
    path('<int:pk>/days/auto-distribute/', plans.auto_distribute, name='auto_distribute'),
]