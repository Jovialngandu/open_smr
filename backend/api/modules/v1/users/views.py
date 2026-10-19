from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import  status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSearchQuerySerializer, UserSearchResultSerializer

User = get_user_model()





@extend_schema(
    tags=['Users'],
    summary='Rechercher un utilisateur',
    description='Recherche partielle sur le username et l’email pour l’autocomplétion frontend.',
    parameters=[
        OpenApiParameter(
            name='q',
            type=str,
            required=False,
            location=OpenApiParameter.QUERY,
            description='Terme de recherche à partir du username ou de l’email.',
        )
    ],
    responses={200: UserSearchResultSerializer(many=True)},
)
class UserSearchPublicAPI(APIView):
    """GET /api/v1/users/search/?q=username_or_email"""
    permission_classes = [AllowAny]

    def get(self, request):
        query_serializer = UserSearchQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        query = (query_serializer.validated_data.get('q') or '').strip()

        if not query:
            return Response([], status=status.HTTP_200_OK)

        users = User.objects.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        ).order_by('username')[:10]

        serializer = UserSearchResultSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
