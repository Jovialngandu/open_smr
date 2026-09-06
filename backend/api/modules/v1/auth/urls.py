from django.urls import path
from api.modules.v1.auth.views import (
    LoginView, 
    CustomTokenRefreshView, 
    UserProfileView, 
    SwitchContextView,
    RegisterView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', LoginView.as_view(), name='auth_login'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='auth_refresh'),
    path('switch-context/', SwitchContextView.as_view(), name='auth_switch_context'),
    path('me/', UserProfileView.as_view(), name='auth_me'),
]