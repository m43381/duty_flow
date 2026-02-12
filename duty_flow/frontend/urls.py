from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('commandant/', views.commandant, name='commandant'),
    path('faculty/', views.faculty, name='faculty'),
    path('department/', views.department, name='department'),
]