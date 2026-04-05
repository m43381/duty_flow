from django.urls import path
from frontend.views import units

# app_name = 'units'

urlpatterns = [
    path('', units.list, name='list'),
    path('add/', units.add, name='add'),
    path('<int:pk>/', units.detail, name='detail'),
    path('<int:pk>/edit/', units.edit, name='edit'),
    path('<int:pk>/delete/', units.delete, name='delete'),
]