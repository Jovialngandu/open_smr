from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .serializers import (
    ScopeInputSerializer, ScopeUpdateSerializer, ScopeOutputSerializer,
    UserScopeAccessSerializer, GrantAccessInputSerializer,RemoveAccessInputSerializer
)
from .selectors import list_scopes_by_organization, get_scope_by_id
from .services import create_scope, update_scope, grant_scope_access, revoke_scope_access


class ScopeListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Lister les Scopes par Organisation", 
        responses={200: ScopeOutputSerializer(many=True)}, 
        parameters=[OpenApiParameter(name='organization_id', type=str, location=OpenApiParameter.QUERY, required=True)]
    )
    def get(self, request):
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({"organization_id": "Ce paramètre est requis."}, status=status.HTTP_400_BAD_REQUEST)

        scopes = list_scopes_by_organization(organization_id=organization_id, user=request.user)
        return Response(ScopeOutputSerializer(scopes, many=True).data)

    @extend_schema(summary="Créer un Scope (Génère 93 entrées SoA)", request=ScopeInputSerializer, responses={201: ScopeOutputSerializer})
    def post(self, request):
        serializer = ScopeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        scope = create_scope(
            organization_id=serializer.validated_data['organization_id'],
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            created_by_user=request.user
        )
        return Response(ScopeOutputSerializer(scope).data, status=status.HTTP_201_CREATED)


class ScopeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Détail d'un Scope", responses={200: ScopeOutputSerializer})
    def get(self, request, pk):
        scope = get_scope_by_id(scope_id=pk, user=request.user)
        return Response(ScopeOutputSerializer(scope).data)

    @extend_schema(summary="Mettre à jour un Scope", request=ScopeUpdateSerializer, responses={200: ScopeOutputSerializer})
    def patch(self, request, pk):
        scope = get_scope_by_id(scope_id=pk, user=request.user)
        serializer = ScopeUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = update_scope(scope=scope, **serializer.validated_data)
        return Response(ScopeOutputSerializer(updated).data)
    
    @extend_schema(summary="Supprimer un Scope", responses={204: None})
    def delete(self, request, pk):
        scope = get_scope_by_id(scope_id=pk, user=request.user)
        scope.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


class SetScopeAccessView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Lister les accès d'un Scope", responses={200: UserScopeAccessSerializer(many=True)})
    def get(self, request, pk):
        scope = get_scope_by_id(scope_id=pk, user=request.user)
        # Correction ici: user_accesses au lieu de accesses
        accesses = scope.user_accesses.select_related('user_organization_role__user', 'granted_by').all()
        return Response(UserScopeAccessSerializer(accesses, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Accorder un accès à un Scope", 
        request=GrantAccessInputSerializer, 
        responses={201: UserScopeAccessSerializer, 200: UserScopeAccessSerializer}
    )
    def post(self, request, pk):
        scope = get_scope_by_id(scope_id=pk, user=request.user)
        serializer = GrantAccessInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        access, created = grant_scope_access(
            scope=scope,
            user_id=serializer.validated_data['user_id'],
            granted_by_user=request.user
        )
        
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(UserScopeAccessSerializer(access).data, status=status_code)

class RemoveScopeAccessView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retirer un accès à un Scope", 
        request=RemoveAccessInputSerializer, 
        responses={204: None}
    )
    def post(self, request, pk):
        scope = get_scope_by_id(scope_id=pk, user=request.user)
        serializer = RemoveAccessInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        revoke_scope_access(
            scope=scope,
            user_id=serializer.validated_data['user_id']
        )
        return Response({"detail": "Accès retiré avec succès."}, status=status.HTTP_200_OK)