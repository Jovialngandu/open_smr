from django.urls import path

from .views import (
    RiskAIAssessmentAPI,
    RiskListCreateAPI,
    RiskDetailAPI,
    RiskIsoControlSuggestionsAPI
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
    path("assess-risk/", RiskAIAssessmentAPI.as_view(), name="assess-risk"),

]

