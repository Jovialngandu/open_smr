from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from api.models import Organization, UserOrganizationRole
from api.modules.v1.organizations.helpers import generate_unique_org_code

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
