from django.urls import path

from .views import (
    RiskListCreateAPI,
    RiskDetailAPI,
    RiskIsoControlSuggestionsAPI
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
    path(
		"<uuid:pk>/iso-control-suggestions/",
		RiskIsoControlSuggestionsAPI.as_view(),
		name="risk-iso-control-suggestions",
	),
]

