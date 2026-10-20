from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework.exceptions import PermissionDenied, ValidationError

from api.models import Organization, OrganizationInvitation, UserOrganizationRole
from api.modules.v1.auth.serializers import build_jwt_payload_for_user
from api.modules.v1.organizations.helpers import generate_unique_org_code
from .backend import OIDCBackend

User = get_user_model()


def check_user_account_status(*, user: User) -> None:
    """Valide la suspension globale et organisationnelle."""
    if not user.is_active:
        raise PermissionDenied("Compte utilisateur suspendu au niveau global.")
    
@transaction.atomic
def register_user(
    *, 
    email: str, 
    username: str, 
    password: str, 
    first_name: str = "", 
    last_name: str = "",
    organization_name: str = None,
    organization_code: str = None,
    join_organization_code: str = None
) -> User:
    """
    Crée un utilisateur dans la base de données.
    Si `organization_name` est fourni, crée l'organisation et attribue le rôle ADMIN.
    Si `join_organization_code` est fourni, rattache le compte comme RISK_OWNER sans
    lui accorder automatiquement de périmètre.
    """
    email = email.lower().strip()
    username = username.strip()

    if User.objects.filter(email=email).exists():
        raise ValidationError({"email": "Un utilisateur avec cet email existe déjà."})

    if User.objects.filter(username=username).exists():
        raise ValidationError({"username": "Ce nom d'utilisateur est déjà pris."})

    # Création du compte utilisateur Django
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=True
    )

    # Création optionnelle de l'organisation
    if organization_name:
        final_code = organization_code if organization_code else generate_unique_org_code(organization_name)

        org = Organization.objects.create(
            name=organization_name,
            code=final_code
        )

        UserOrganizationRole.objects.create(
            user=user,
            organization=org,
            role='ADMIN',
            is_active=True
        )
    elif join_organization_code:
        organization = Organization.objects.get(code__iexact=join_organization_code.strip())
        UserOrganizationRole.objects.create(
            user=user,
            organization=organization,
            role='RISK_OWNER',
            is_active=True
        )

    return user


def _generate_unique_username(email: str) -> str:
    base = (email.split('@')[0] or 'user').strip().lower().replace('.', '_').replace('+', '_')[:30]
    username = base or 'user'
    counter = 1
    while User.objects.filter(username__iexact=username).exists():
        username = f'{base}{counter}'
        counter += 1
    return username


@transaction.atomic
def authenticate_oidc_user(*, id_token: str, provider: str = 'google') -> dict:
    """Valide un JWT OIDC Google et authentifie ou crée localement l'utilisateur."""
    claims = OIDCBackend.authenticate(id_token=id_token, provider=provider)
    email = (claims.get('email') or '').strip().lower()

    if not email:
        raise ValidationError({'email': 'Le fournisseur OIDC n’a pas renvoyé d’adresse e-mail valide.'})

    # 1. CAS : L'utilisateur existe déjà en base de données
    user = User.objects.filter(email__iexact=email).first()
    if user:
        if not user.is_active:
            raise PermissionDenied('Compte utilisateur désactivé.')
        return {'user': user, 'tokens': build_jwt_payload_for_user(user)}

    # 2. CAS : L'utilisateur n'existe pas -> Création de l'utilisateur
    username = _generate_unique_username(email)
    first_name = (claims.get('first_name') or '').strip() or 'Google'
    last_name = (claims.get('last_name') or '').strip() or 'User'

    user = User.objects.create_user(
        username=username,
        email=email,
        password=get_random_string(length=24),
        first_name=first_name,
        last_name=last_name,
        is_active=True,
    )

    # 2a. Vérification d'une invitation B2B en attente
    invitation = OrganizationInvitation.objects.filter(
        invited_user_email__iexact=email,
        status=OrganizationInvitation.Status.PENDING,
        expires_at__gt=timezone.now(),
    ).order_by('-created_at').first()

    if invitation:
        UserOrganizationRole.objects.create(
            user=user,
            organization=invitation.organization,
            role=invitation.role,
            is_active=True,
        )
        invitation.status = OrganizationInvitation.Status.ACCEPTED
        invitation.save(update_fields=['status'])
    else:
        # 2b. Signup Public : Générer un code d'organisation unique pour éviter l'IntegrityError !
        org_name = f"Organisation de {first_name} {last_name}".strip()
        org_code = generate_unique_org_code(org_name)  # Utilise ta fonction de génération de code

        organization = Organization.objects.create(
            name=org_name,
            code=org_code,
        )

        UserOrganizationRole.objects.create(
            user=user,
            organization=organization,
            role='ADMIN',
            is_active=True,
        )

    return {'user': user, 'tokens': build_jwt_payload_for_user(user)}