from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema,OpenApiResponse

from api.modules.v1.auth.serializers import (
    CustomTokenObtainPairSerializer, 
    UserProfileSerializer, 
    SwitchContextSerializer,
    build_jwt_payload_for_user,
    RegisterResponseSerializer,
    RegisterSerializer
)
from api.modules.v1.auth.selectors import get_user_by_id
from api.modules.v1.permissions import IsAccountActive
from api.modules.v1.auth.services import register_user


@extend_schema(
	tags=['Authentication'],
	request=CustomTokenObtainPairSerializer,
	responses={
		200: OpenApiResponse(description="Connexion réussie, retourne les tokens JWT."),
		401: OpenApiResponse(description="Échec de l'authentification (email/mot de passe incorrect).")
	}
)
class LoginView(TokenObtainPairView):
    """POST /api/v1/auth/login/"""
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(tags=['Authentication'])
class CustomTokenRefreshView(TokenRefreshView):
    """Rafraîchissement du token d'accès JWT."""
    permission_classes = [AllowAny]

@extend_schema(
	tags=['Authentication'],
	request=SwitchContextSerializer,
	responses={
		200: OpenApiResponse(description="Changement de contexte réussi, retourne les nouveaux tokens JWT."),
		400: OpenApiResponse(description="Erreur de validation (organisation ou périmètre invalide)."),
		403: OpenApiResponse(description="L'utilisateur n'a pas accès à l'organisation ou au périmètre spécifié.")
	}
)
class SwitchContextView(APIView):
    """
    POST /api/v1/auth/switch-context/
    Permet à l'utilisateur de régénérer ses tokens JWT pour cibler 
    une autre organisation ou un autre périmètre (Scope).
    """
    permission_classes = [IsAuthenticated, IsAccountActive]

    @extend_schema(request=SwitchContextSerializer,tags=['Authentication'])
    def post(self, request):
        serializer = SwitchContextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org_id = serializer.validated_data.get('organization_id')
        scope_id = serializer.validated_data.get('scope_id')

        refresh = build_jwt_payload_for_user(request.user, organization_id=org_id, scope_id=scope_id)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'active_organization_id': str(org_id),
            'active_scope_id': str(scope_id) if scope_id else None
        }, status=status.HTTP_200_OK)


@extend_schema(
	tags=['Authentication'],
	responses={200: UserProfileSerializer}
)
class UserProfileView(APIView):
    """GET /api/v1/auth/me/"""
    permission_classes = [IsAuthenticated, IsAccountActive]

    def get(self, request):
        user = get_user_by_id(user_id=request.user.id)
        if not user:
            return Response({"detail": "Utilisateur non trouvé ou inactif."}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = UserProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
@extend_schema(
    tags=['Authentication'],
    request=RegisterSerializer,
    responses={
        201: RegisterResponseSerializer,
        400: OpenApiResponse(description="Erreur de validation (email/username déjà pris, mot de passe trop faible, etc.)")
    }
)
class RegisterView(APIView):
    """
    Endpoint POST /api/v1/auth/register/
    Crée un compte utilisateur et retourne immédiatement ses tokens JWT ainsi que son profil.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = register_user(
            email=serializer.validated_data['email'],
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', ''),
            organization_name=serializer.validated_data.get('organization_name')
        )

        # Génération directe des tokens après inscription réussie
        refresh = build_jwt_payload_for_user(user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)