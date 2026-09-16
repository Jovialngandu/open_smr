from django.urls import path

from .views import (
    RiskListCreateAPI,
    RiskDetailAPI,
)


urlpatterns = [
    path(
        "",
        RiskListCreateAPI.as_view(),
        name="risk-list-create",
    ),
    path(
        "<uuid:pk>/",
        RiskDetailAPI.as_view(),
        name="risk-detail",
    ),
]

