from django.urls import path

from .views import (
    AssetListCreateAPI,
    AssetDetailAPI,
)


app_name = "assets"


urlpatterns = [
    path(
        "",
        AssetListCreateAPI.as_view(),
        name="asset-list-create",
    ),

    path(
        "<uuid:pk>/",
        AssetDetailAPI.as_view(),
        name="asset-detail",
    ),
]