from django.urls import path
from api.modules.v1.heatmap.views import HeatmapView

urlpatterns = [
    path('', HeatmapView.as_view(), name='heatmap-matrix'),
]