from django.urls import path, include

urlpatterns = [
    path('', include(('frontend.urls.auth', 'auth'), namespace='auth')),
    path('persons/', include(('frontend.urls.people', 'people'), namespace='people')),
    path('plans/', include(('frontend.urls.plans', 'plans'), namespace='plan')),
    path('types/', include(('frontend.urls.duty_types', 'duty_types'), namespace='type')),
    path('unit-types/', include(('frontend.urls.unit_types', 'unit_types'), namespace='unit_type')),
    path('units/', include(('frontend.urls.units', 'units'), namespace='units')),
    path('users/', include(('frontend.urls.users', 'users'), namespace='users')),
    path('assignments/', include(('frontend.urls.assignments', 'assignments'), namespace='assignment')),
]