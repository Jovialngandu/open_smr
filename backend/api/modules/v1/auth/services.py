from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from api.models import Organization, UserOrganizationRole

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
    organization_name: str = None
) -> User:
    """
    Crée un utilisateur dans la base de données.
    Si `organization_name` est fourni, crée également l'organisation et 
    attribue le rôle ADMIN à l'utilisateur au sein de cette organisation.
    """
    email = email.lower().strip()
    username = username.strip()

    if User.objects.filter(email=email).exists():
        raise ValidationError({"email": "Un utilisateur avec cet email existe déjà."})

    if User.objects.filter(username=username).exists():
        raise ValidationError({"username": "Ce nom d'utilisateur est déjà pris."})

    # Création du compte utilisateur
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=True
    )

    # Optionnel : Création automatique d'une première organisation si spécifiée lors du register
    if organization_name:
        org = Organization.objects.create(name=organization_name)
        UserOrganizationRole.objects.create(
            user=user,
            organization=org,
            role='ADMIN',
            is_active=True
        )

    return user