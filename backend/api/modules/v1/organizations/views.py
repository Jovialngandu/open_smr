from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .selectors import get_organization_by_id, list_user_organizations, get_organization_members
from .services import create_organization, update_organization, assign_user_role, toggle_member_active_status
from .serializers import (
    OrganizationInputSerializer,
    OrganizationOutputSerializer,
    MemberRoleAssignmentSerializer,
    ToggleActiveStatusSerializer
)
from ..permissions import IsAdminRole


class OrganizationListCreateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Lister mes organisations",
        responses={200: OrganizationOutputSerializer(many=True)}
    )
    def get(self, request):
        orgs = list_user_organizations(request.user)
        serializer = OrganizationOutputSerializer(orgs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Créer une nouvelle organisation",
        request=OrganizationInputSerializer,
        responses={201: OrganizationOutputSerializer}
    )
    def post(self, request):
        serializer = OrganizationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        org = create_organization(
            **serializer.validated_data,
            owner_user=request.user
        )
        return Response(OrganizationOutputSerializer(org).data, status=status.HTTP_201_CREATED)


class OrganizationDetailAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    @extend_schema(
        summary="Détails d'une organisation",
        responses={200: OrganizationOutputSerializer}
    )
    def get(self, request, pk):
        org = get_organization_by_id(pk)
        return Response(OrganizationOutputSerializer(org).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Mettre à jour une organisation",
        request=OrganizationInputSerializer,
        responses={200: OrganizationOutputSerializer}
    )
    def put(self, request, pk):
        org = get_organization_by_id(pk)
        serializer = OrganizationInputSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        updated_org = update_organization(organization=org, **serializer.validated_data)
        return Response(OrganizationOutputSerializer(updated_org).data, status=status.HTTP_200_OK)


class OrganizationMembersAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    @extend_schema(
        summary="Lister les membres d'une organisation",
        responses={200: MemberRoleAssignmentSerializer(many=True)}
    )
    def get(self, request, org_id):
        members = get_organization_members(org_id)
        return Response(MemberRoleAssignmentSerializer(members, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Affecter ou modifier le rôle d'un membre",
        request=MemberRoleAssignmentSerializer,
        responses={200: MemberRoleAssignmentSerializer}
    )
    def post(self, request, org_id):
        serializer = MemberRoleAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        member = assign_user_role(
            org_id=org_id,
            user_id=serializer.validated_data['user_id'],
            role=serializer.validated_data['role']
        )
        return Response(MemberRoleAssignmentSerializer(member).data, status=status.HTTP_200_OK)


class MemberStatusToggleAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    @extend_schema(
        summary="Suspendre ou activer le statut d'un membre",
        request=ToggleActiveStatusSerializer,
        responses={200: MemberRoleAssignmentSerializer}
    )
    def patch(self, request, org_id, role_id):
        serializer = ToggleActiveStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        member = toggle_member_active_status(
            role_id=role_id,
            is_active=serializer.validated_data['is_active']
        )
        return Response(MemberRoleAssignmentSerializer(member).data, status=status.HTTP_200_OK)