from django.urls import path, include

urlpatterns = [
    path('v1/auth/', include('api.modules.v1.auth.urls')),
]