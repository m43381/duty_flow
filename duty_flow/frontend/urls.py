from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cabinet/commandant/', views.commandant_cabinet, name='commandant_cabinet'),
    path('cabinet/faculty/', views.faculty_cabinet, name='faculty_cabinet'),
    path('cabinet/department/', views.department_cabinet, name='department_cabinet'),
]