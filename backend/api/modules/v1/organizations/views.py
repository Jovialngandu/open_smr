from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import OrganizationInvitation, UserOrganizationRole

from .selectors import (
    get_organization_by_id,
    get_pending_invitation_by_token,
    list_user_organizations,
    get_organization_members,
)
from .services import (
    accept_organization_invitation,
    assign_user_role,
    create_organization,
    create_organization_invitation,
    decline_organization_invitation,
    delete_organization,
    toggle_member_active_status,
    update_organization,
)
from .serializers import (
    OrganizationInputSerializer,
    OrganizationInvitationAcceptSerializer,
    OrganizationInvitationCreateSerializer,
    OrganizationInvitationDeclineSerializer,
    OrganizationInvitationSerializer,
    OrganizationOutputSerializer,
    MemberRoleAssignmentSerializer,
    ToggleActiveStatusSerializer,
)
from ..permissions import IsAdminRole, IsRssiRole

User = get_user_model()


@extend_schema(tags=['Organizations'])
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


@extend_schema(tags=['Organizations'])
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

    @extend_schema(
        summary="Supprimer une organisation",
        responses={204: None}
    )
    def delete(self, request, pk):
        org = get_organization_by_id(pk)
        if request.user.is_superuser:
            org.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if not org.user_roles.filter(user=request.user, is_active=True, role='ADMIN').exists():
            raise PermissionDenied("Vous devez être le propriétaire de l'organisation pour la supprimer.")

        org.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['Organizations'])
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


@extend_schema(tags=['Organizations'])
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


@extend_schema(tags=['Organizations'])
class OrganizationInvitationCreateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, IsRssiRole]

    @extend_schema(
        summary="Créer une invitation vers une organisation",
        request=OrganizationInvitationCreateSerializer,
        responses={201: OrganizationInvitationSerializer}
    )
    def post(self, request, org_id):
        org = get_organization_by_id(org_id)
        serializer = OrganizationInvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not UserOrganizationRole.objects.filter(
            user=request.user,
            organization=org,
            is_active=True,
            role__in=['ADMIN', 'RSSI'],
        ).exists():
            raise PermissionDenied('Vous devez être ADMIN ou RSSI pour inviter un membre.')

        invitation = create_organization_invitation(
            organization=org,
            invited_by=request.user,
            invited_user_email=serializer.validated_data['invited_user_email'],
            role=serializer.validated_data.get('role', OrganizationInvitation.Role.RISK_OWNER),
        )

        return Response(OrganizationInvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Organizations'])
class OrganizationInvitationAcceptAPI(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Accepter une invitation d'organisation",
        request=OrganizationInvitationAcceptSerializer,
        responses={200: OrganizationInvitationSerializer},
    )
    def post(self, request):
        serializer = OrganizationInvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = str(serializer.validated_data['token'])
        user = request.user if request.user and request.user.is_authenticated else None
        invitation = accept_organization_invitation(token=token, user=user)

        return Response({
            'detail': 'Invitation acceptée.',
            'invitation': OrganizationInvitationSerializer(invitation).data,
        }, status=status.HTTP_200_OK)


@extend_schema(tags=['Organizations'])
class OrganizationInvitationDeclineAPI(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Refuser une invitation d'organisation",
        request=OrganizationInvitationDeclineSerializer,
        responses={200: OrganizationInvitationSerializer},
    )
    def post(self, request):
        serializer = OrganizationInvitationDeclineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = str(serializer.validated_data['token'])
        user = request.user if request.user and request.user.is_authenticated else None
        invitation = decline_organization_invitation(token=token, user=user)

        return Response({
            'detail': 'Invitation refusée.',
            'invitation': OrganizationInvitationSerializer(invitation).data,
        }, status=status.HTTP_200_OK)