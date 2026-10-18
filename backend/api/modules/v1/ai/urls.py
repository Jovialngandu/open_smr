from django.urls import path
from api.modules.v1.ai.views import SoaVectorSearchView

urlpatterns = [
    path('ai/soa-search/', SoaVectorSearchView.as_view(), name='soa-vector-search'),
]