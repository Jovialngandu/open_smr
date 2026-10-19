import uuid
from datetime import timedelta
from uuid import UUID

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from api.models import EmailLog, Organization, OrganizationInvitation, UserOrganizationRole
from api.modules.v1.emails.services import send_email
from .helpers import generate_unique_org_code

User = get_user_model()


@transaction.atomic
def create_organization(*, name: str, description: str = "", owner_user) -> Organization:
    """Crée une organisation avec un code unique et le propriétaire comme ADMIN."""
    code = generate_unique_org_code(name)

    org = Organization.objects.create(
        name=name,
        code=code,
        description=description,
    )

    UserOrganizationRole.objects.create(
        user=owner_user,
        organization=org,
        role='ADMIN',
        is_active=True,
    )

    return org


@transaction.atomic
def update_organization(*, organization: Organization, name: str = None, description: str = None) -> Organization:
    """Met à jour les informations modifiables de l'organisation."""
    if name is not None:
        organization.name = name

    if description is not None:
        organization.description = description

    organization.save()
    return organization


@transaction.atomic
def assign_user_role(*, org_id: UUID, user_id: UUID, role: str) -> UserOrganizationRole:
    """Assigne ou met à jour le rôle d'un utilisateur dans une organisation."""
    user_role, _ = UserOrganizationRole.objects.update_or_create(
        organization_id=org_id,
        user_id=user_id,
        defaults={'role': role, 'is_active': True},
    )
    return user_role


@transaction.atomic
def toggle_member_active_status(*, role_id: UUID, is_active: bool) -> UserOrganizationRole:
    """Active ou suspend l'accès d'un membre dans l'organisation."""
    user_role = UserOrganizationRole.objects.get(id=role_id)
    user_role.is_active = is_active
    user_role.save()
    return user_role


@transaction.atomic
def delete_organization(*, organization: Organization, user) -> None:
    """Supprime une organisation uniquement si l'utilisateur est bien son propriétaire (ADMIN actif)."""
    if user.is_superuser:
        organization.delete()
        return

    is_owner = UserOrganizationRole.objects.filter(
        user=user,
        organization=organization,
        is_active=True,
        role='ADMIN',
    ).exists()

    if not is_owner:
        raise PermissionError("Vous devez être le propriétaire de l'organisation pour la supprimer.")

    organization.delete()


@transaction.atomic
def create_organization_invitation(*, organization: Organization, invited_by, invited_user_email: str, role: str = OrganizationInvitation.Role.RISK_OWNER) -> OrganizationInvitation:
    """Crée une invitation d'organisation avec token UUID, rôle choisi et expiration de 7 jours."""
    email = (invited_user_email or '').strip().lower()
    if not email:
        raise ValidationError({'invited_user_email': 'L’adresse email est obligatoire.'})

    valid_role = role or OrganizationInvitation.Role.RISK_OWNER
    if valid_role not in dict(OrganizationInvitation.Role.choices):
        raise ValidationError({'role': 'Le rôle choisi n’est pas valide.'})

    existing_pending = OrganizationInvitation.objects.filter(
        organization=organization,
        invited_user_email__iexact=email,
        status=OrganizationInvitation.Status.PENDING,
    ).exists()
    if existing_pending:
        raise ValidationError({'invited_user_email': 'Une invitation en attente existe déjà pour cet email.'})

    invitation = OrganizationInvitation.objects.create(
        organization=organization,
        invited_by=invited_by,
        invited_user_email=email,
        token=uuid.uuid4(),
        role=valid_role,
        status=OrganizationInvitation.Status.PENDING,
        expires_at=timezone.now() + timedelta(days=7),
    )

    send_organization_invitation_email(invitation)
    return invitation


def send_organization_invitation_email(invitation: OrganizationInvitation) -> bool:
    """Envoie l’e-mail d’invitation via le service de mail générique."""
    frontend_url = settings.FRONTEND_URL.rstrip('/')
    invitation_url = f"{frontend_url}/invitations?token={invitation.token}"
    context = {
        'organization_name': invitation.organization.name,
        'inviter_name': invitation.invited_by.get_full_name() or invitation.invited_by.username,
        'invited_user_email': invitation.invited_user_email,
        'invitation_url': invitation_url,
        'expires_at': invitation.expires_at.strftime('%d/%m/%Y à %H:%M'),
        'frontend_url': frontend_url,
    }
    return send_email(
        recipient_email=invitation.invited_user_email,
        subject=f"Invitation à rejoindre {invitation.organization.name}",
        template_name='organization_invitation_email.html',
        context=context,
        email_type=EmailLog.EmailType.INVITATION,
        user=invitation.invited_by,
        organization=invitation.organization,
    )


@transaction.atomic
def accept_organization_invitation(*, token: str, user) -> OrganizationInvitation:
    """Accepte une invitation par token, vérifie la validité et ajoute l'utilisateur à l'organisation."""
    invitation = OrganizationInvitation.objects.select_related('organization', 'invited_by').get(token=token)

    if invitation.status != OrganizationInvitation.Status.PENDING:
        raise ValidationError({'token': 'Cette invitation n’est plus active.'})

    if invitation.expires_at < timezone.now():
        invitation.status = OrganizationInvitation.Status.DECLINED
        invitation.save(update_fields=['status'])
        raise ValidationError({'token': 'Cette invitation a expiré.'})

    if user is not None and user.email.lower() != invitation.invited_user_email.lower():
        raise PermissionDenied('Vous n’êtes pas le destinataire de cette invitation.')

    invitation_role = invitation.role or OrganizationInvitation.Role.RISK_OWNER
    if user is not None:
        UserOrganizationRole.objects.update_or_create(
            organization=invitation.organization,
            user=user,
            defaults={'role': invitation_role, 'is_active': True},
        )

    invitation.status = OrganizationInvitation.Status.ACCEPTED
    invitation.save(update_fields=['status'])
    return invitation


@transaction.atomic
def decline_organization_invitation(*, token: str, user=None) -> OrganizationInvitation:
    """Refuse une invitation par token."""
    invitation = OrganizationInvitation.objects.select_related('organization', 'invited_by').get(token=token)

    if invitation.status != OrganizationInvitation.Status.PENDING:
        raise ValidationError({'token': 'Cette invitation n’est plus active.'})

    if user is not None and user.email.lower() != invitation.invited_user_email.lower():
        raise PermissionDenied('Vous n’êtes pas le destinataire de cette invitation.')

    invitation.status = OrganizationInvitation.Status.DECLINED
    invitation.save(update_fields=['status'])
    return invitation