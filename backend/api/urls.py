from django.urls import path, include

urlpatterns = [
    path('v1/auth/', include('api.modules.v1.auth.urls')),
    path('v1/organizations/', include('api.modules.v1.organizations.urls')),
    path('v1/scopes/', include('api.modules.v1.scopes.urls')),
    path('settings/', include('api.modules.v1.settings.urls')),
    path('v1/treatment/', include('api.modules.v1.treatment.urls')),
    path('v1/heatmap/', include('api.modules.v1.heatmap.urls')),
    path("v1/soa/", include("api.modules.v1.soa.urls")),
]