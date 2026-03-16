from django.urls import path
from . import views_person

app_name = 'person'

urlpatterns = [
    path('', views_person.person_list, name='person_list'),
    path('add/', views_person.person_add, name='person_add'),
    path('<int:pk>/', views_person.person_detail, name='person_detail'),  # <-- здесь pk
    path('<int:pk>/edit/', views_person.person_edit, name='person_edit'),  # <-- здесь pk
    path('<int:pk>/delete/', views_person.person_delete, name='person_delete'),  # <-- здесь pk
]