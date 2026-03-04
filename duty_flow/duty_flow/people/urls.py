from django.urls import path
from . import views

app_name = 'people'

urlpatterns = [
    path('', views.person_list, name='person_list'),
    path('create/', views.person_create, name='person_create'),
    path('<int:pk>/', views.person_detail, name='person_detail'),
    path('<int:pk>/update/', views.person_update, name='person_update'),
    path('<int:pk>/delete/', views.person_delete, name='person_delete'),
]