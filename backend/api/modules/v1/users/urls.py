from django.urls import path

from api.modules.v1.users.views import UserSearchPublicAPI

urlpatterns = [
    path('search/', UserSearchPublicAPI.as_view(), name='user-search-public'),
]
