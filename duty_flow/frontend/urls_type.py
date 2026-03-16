from django.urls import path
from . import views_type

app_name = 'type'

urlpatterns = [
    path('', views_type.type_list, name='type_list'),
    path('add/', views_type.type_add, name='type_add'),
    path('<int:pk>/', views_type.type_detail, name='type_detail'),
    path('<int:pk>/edit/', views_type.type_edit, name='type_edit'),
    path('<int:pk>/delete/', views_type.type_delete, name='type_delete'),
]