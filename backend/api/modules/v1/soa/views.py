from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.models import Scope, SoaEntry, UserScopeAccess

from .selectors import (
    get_soa_entries_by_scope,
    list_soa_versions,
)
from .serializers import (
    SoaEntryUpdateSerializer,
    SoaVersionCreateSerializer,
    SoaVersionOutputSerializer,
)
from .services import (
    update_soa_entry,
    create_soa_snapshot_version,
)


def check_scope_access(user, scope):
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


class SoaEntryListAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Lister les entrées SoA d'un périmètre",
        parameters=[
            OpenApiParameter(
                name="scope_id",
                type=str,
                required=True,
                description="UUID du périmètre",
            ),
        ],
    )
    def get(self, request):
        scope_id = request.query_params.get("scope_id")

        if not scope_id:
            return Response(
                {"scope_id": "Ce paramètre est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        scope = get_object_or_404(Scope, id=scope_id)

        check_scope_access(request.user, scope)

        entries = get_soa_entries_by_scope(scope.id)

        data = []

        for entry in entries:
            data.append(
                {
                    "id": str(entry.id),
                    "scope": str(entry.scope_id),
                    "iso_control": {
                        "id": str(entry.iso_control.id),
                        "code": entry.iso_control.code,
                        "title": entry.iso_control.title,
                        "theme": entry.iso_control.theme,
                    },
                    "is_applicable": entry.is_applicable,
                    "justification": entry.justification,
                    "implementation_status": entry.implementation_status,
                    "created_at": entry.created_at,
                    "updated_at": entry.updated_at,
                }
            )

        return Response(data, status=status.HTTP_200_OK)


class SoaEntryDetailAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_entry(self, request, pk):
        entry = get_object_or_404(
            SoaEntry.objects.select_related(
                "scope",
                "iso_control",
            ),
            id=pk,
        )

        check_scope_access(request.user, entry.scope)

        return entry

    @extend_schema(
        summary="Modifier une entrée SoA",
        request=SoaEntryUpdateSerializer,
    )
    def patch(self, request, pk):
        entry = self.get_entry(request, pk)

        serializer = SoaEntryUpdateSerializer(
            entry,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        updated_entry = update_soa_entry(
            soa_entry=entry,
            **serializer.validated_data,
        )

        return Response(
            {
                "id": str(updated_entry.id),
                "scope": str(updated_entry.scope_id),
                "iso_control": {
                    "id": str(updated_entry.iso_control.id),
                    "code": updated_entry.iso_control.code,
                    "title": updated_entry.iso_control.title,
                    "theme": updated_entry.iso_control.theme,
                },
                "is_applicable": updated_entry.is_applicable,
                "justification": updated_entry.justification,
                "implementation_status": updated_entry.implementation_status,
                "updated_at": updated_entry.updated_at,
            },
            status=status.HTTP_200_OK,
        )


class SoaVersionListCreateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Lister les versions SoA d'un périmètre",
        parameters=[
            OpenApiParameter(
                name="scope_id",
                type=str,
                required=True,
                description="UUID du périmètre",
            ),
        ],
        responses={200: SoaVersionOutputSerializer(many=True)},
    )
    def get(self, request):
        scope_id = request.query_params.get("scope_id")

        if not scope_id:
            return Response(
                {"scope_id": "Ce paramètre est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        scope = get_object_or_404(Scope, id=scope_id)

        check_scope_access(request.user, scope)

        versions = list_soa_versions(scope.id)

        serializer = SoaVersionOutputSerializer(
            versions,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Créer une version snapshot de la SoA",
        request=SoaVersionCreateSerializer,
        responses={201: SoaVersionOutputSerializer},
    )
    
    def post(self, request):
        scope_id = request.data.get("scope_id")
        version_number = request.data.get("version_number")
        title = request.data.get("title")
        version_status = request.data.get(
            "status",
            "DRAFT",
        )

        if not scope_id:
            return Response(
                {"scope_id": "Ce champ est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not version_number:
            return Response(
                {"version_number": "Ce champ est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not title:
            return Response(
                {"title": "Ce champ est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        scope = get_object_or_404(
            Scope,
            id=scope_id,
        )

        check_scope_access(request.user, scope)

        approved_by = None

        if version_status == "APPROVED":
            approved_by = request.user

        soa_version = create_soa_snapshot_version(
            scope=scope,
            version_number=version_number,
            title=title,
            approved_by=approved_by,
            status=version_status,
        )

        serializer = SoaVersionOutputSerializer(
            soa_version
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )



    