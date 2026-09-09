from django.urls import path, include

urlpatterns = [
    path('v1/auth/', include('api.modules.v1.auth.urls')),
    path('v1/organizations/', include('api.modules.v1.organizations.urls')),
    path('v1/assets/', include('api.modules.v1.assets.urls')),
]