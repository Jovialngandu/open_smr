from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema

from api.modules.v1.settings.selectors import (
    get_user_preferences, 
    list_system_settings, 
    get_system_setting_by_key
)
from api.modules.v1.settings.services import (
    update_user_preferences, 
    update_system_setting
)
from api.modules.v1.settings.serializers import (
    UserPreferenceSerializer, 
    SystemSettingSerializer, 
    UpdateSystemSettingInputSerializer
)


class UserPreferenceMeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Obtenir les préférences de l'utilisateur connecté",
        responses={200: UserPreferenceSerializer}
    )
    def get(self, request):
        preferences = get_user_preferences(user=request.user)
        return Response(UserPreferenceSerializer(preferences).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Mettre à jour les préférences de l'utilisateur connecté",
        request=UserPreferenceSerializer,
        responses={200: UserPreferenceSerializer}
    )
    def patch(self, request):
        serializer = UserPreferenceSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        updated_preferences = update_user_preferences(
            user=request.user, 
            data=serializer.validated_data
        )
        return Response(UserPreferenceSerializer(updated_preferences).data, status=status.HTTP_200_OK)


class SystemSettingListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        summary="Lister tous les paramètres système (Admin)",
        responses={200: SystemSettingSerializer(many=True)}
    )
    def get(self, request):
        settings_list = list_system_settings()
        return Response(SystemSettingSerializer(settings_list, many=True).data, status=status.HTTP_200_OK)


class SystemSettingDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        summary="Mettre à jour un paramètre système par sa clé (Admin)",
        request=UpdateSystemSettingInputSerializer,
        responses={200: SystemSettingSerializer}
    )
    def patch(self, request, key):
        serializer = UpdateSystemSettingInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        setting = update_system_setting(
            key=key,
            value=serializer.validated_data['value'],
            description=serializer.validated_data.get('description')
        )
        return Response(SystemSettingSerializer(setting).data, status=status.HTTP_200_OK)