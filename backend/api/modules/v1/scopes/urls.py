from django.urls import path
from .views import ScopeListCreateView, ScopeDetailView,  SetScopeAccessView,RemoveScopeAccessView

urlpatterns = [
    path('', ScopeListCreateView.as_view(), name='scope-list-create'),
    path('<uuid:pk>/', ScopeDetailView.as_view(), name='scope-detail'),
    path('<uuid:pk>/access/', SetScopeAccessView.as_view(), name='scope-access'),
    path('<uuid:pk>/access/remove/', RemoveScopeAccessView.as_view(), name='scope-access-remove'),
	]