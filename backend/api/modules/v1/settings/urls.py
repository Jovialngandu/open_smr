from django.urls import path
from api.modules.v1.settings.views import (
    UserPreferenceMeView,
    SystemSettingListView,
    SystemSettingDetailView
)

urlpatterns = [
    path('me/', UserPreferenceMeView.as_view(), name='user-preferences-me'),
    path('system/', SystemSettingListView.as_view(), name='system-settings-list'),
    path('system/<str:key>/', SystemSettingDetailView.as_view(), name='system-settings-detail'),
]