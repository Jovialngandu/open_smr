from django.urls import path

from .views import (
    SoaEntryListAPI,
    SoaEntryDetailAPI,
    SoaVersionListCreateAPI,
)


urlpatterns = [
    path(
        "entries/",
        SoaEntryListAPI.as_view(),
        name="soa-entry-list",
    ),
    path(
        "entries/<uuid:pk>/",
        SoaEntryDetailAPI.as_view(),
        name="soa-entry-detail",
    ),
    path(
        "versions/",
        SoaVersionListCreateAPI.as_view(),
        name="soa-version-list-create",
    ),
]