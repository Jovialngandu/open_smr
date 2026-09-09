from django.shortcuts import get_object_or_404

from rest_framework import status, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.models import Scope, UserScopeAccess
from api.models import Asset, Scope, UserScopeAccess

from .selectors import (
    get_asset_by_id,
    list_assets_by_scope,
    filter_assets_by_category,
)
from .services import (
    create_asset,
    update_asset,
    delete_asset,
)
from .serializers import (
    AssetSerializer,
    AssetCreateSerializer,
    AssetUpdateSerializer,
)


def check_scope_access(user, scope):
    """
    Vérifie que l'utilisateur a le droit d'accéder au scope.
    """

    if user.is_superuser:
        return

    has_access = UserScopeAccess.objects.filter(
        user_organization_role__user=user,
        user_organization_role__is_active=True,
        scope=scope,
    ).exists()

    if not has_access:
        raise PermissionDenied(
            "Vous n'avez pas accès à ce périmètre."
        )


class AssetListCreateAPI(APIView):
    """
    Liste ou crée les actifs.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Lister les actifs d'un périmètre",
        parameters=[
            OpenApiParameter(
                name="scope_id",
                type=str,
                required=True,
                description="UUID du périmètre",
            ),
            OpenApiParameter(
                name="category",
                type=str,
                required=False,
                description="Catégorie de l'actif",
            ),
        ],
        responses={200: AssetSerializer(many=True)},
    )

    def get(self, request):

        scope_id = request.query_params.get("scope_id")
        category = request.query_params.get("category")

        if not scope_id:
            raise ValidationError({
                "scope_id": "Ce paramètre est obligatoire."
            })

        scope = get_object_or_404(Scope, id=scope_id)

        check_scope_access(request.user, scope)

        if category:
            assets = filter_assets_by_category(
                scope_id=scope.id,
                category=category,
            )
        else:
            assets = list_assets_by_scope(
                scope_id=scope.id
            )

        serializer = AssetSerializer(
            assets,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Créer un actif",
        request=AssetCreateSerializer,
        responses={201: AssetSerializer},
    )
    
    def post(self, request):

        serializer = AssetCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        scope = get_object_or_404(
            Scope,
            id=data["scope_id"]
        )

        check_scope_access(
            request.user,
            scope
        )

        owner = request.user

        asset = create_asset(
            scope=scope,
            owner=owner,
            name=data["name"],
            category=data["category"],
            description=data.get("description"),
            confidentiality=data.get(
                "confidentiality",
                1
            ),
            integrity=data.get(
                "integrity",
                1
            ),
            availability=data.get(
                "availability",
                1
            ),
        )

        return Response(
            AssetSerializer(asset).data,
            status=status.HTTP_201_CREATED
        )


class AssetDetailAPI(APIView):
    """
    Affiche, modifie ou supprime un actif.
    """

    permission_classes = [permissions.IsAuthenticated]



    def get_asset(self, request, pk):

        try:
            asset = get_asset_by_id(pk)
        except Exception:
            raise ValidationError({
                "asset": "Actif introuvable."
            })

        check_scope_access(
            request.user,
            asset.scope
        )

        return asset



    @extend_schema(
        summary="Afficher un actif",
        responses={200: AssetSerializer},
    )

    def get(self, request, pk):

        asset = self.get_asset(
            request,
            pk
        )

        return Response(
            AssetSerializer(asset).data,
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Modifier un actif",
        request=AssetUpdateSerializer,
        responses={200: AssetSerializer},
    )

    def patch(self, request, pk):

        asset = self.get_asset(
            request,
            pk
        )

        serializer = AssetUpdateSerializer(
            data=request.data,
            partial=True
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        updated_asset = update_asset(
            asset=asset,
            name=data.get("name"),
            category=data.get("category"),
            description=data.get("description"),
            confidentiality=data.get("confidentiality"),
            integrity=data.get("integrity"),
            availability=data.get("availability"),
        )

        return Response(
            AssetSerializer(updated_asset).data,
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Supprimer un actif",
        responses={204: None},
    )

    def delete(self, request, pk):

        asset = self.get_asset(
            request,
            pk
        )

        delete_asset(asset=asset)

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


