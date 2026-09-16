# api/modules/v1/soa/urls.py
from django.urls import path
from .views import SoaExportAPIView

urlpatterns = [
    # Utilisation du type <uuid:scope_id> au lieu d'un entier ou de la route sans type
    path('scopes/<uuid:scope_id>/export/', SoaExportAPIView.as_view(), name='soa-export'),
]


