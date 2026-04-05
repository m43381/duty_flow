from django.urls import path, include

urlpatterns = [
    path('', include(('core.urls.auth', 'auth'), namespace='auth')),
    path('persons/', include(('core.urls.people', 'people'), namespace='people')),
    path('plans/', include(('core.urls.plans', 'plans'), namespace='plan')),
    path('types/', include(('core.urls.duty_types', 'duty_types'), namespace='type')),
    path('unit-types/', include(('core.urls.unit_types', 'unit_types'), namespace='unit_type')),
    path('units/', include(('core.urls.units', 'units'), namespace='units')),
    path('users/', include(('core.urls.users', 'users'), namespace='users')),
    path('assignments/', include(('core.urls.assignments', 'assignments'), namespace='assignment')),
]