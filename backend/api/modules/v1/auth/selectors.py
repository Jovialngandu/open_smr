from django.contrib.auth import get_user_model
from api.models import UserOrganizationRole

User = get_user_model()


def get_user_by_id(*, user_id: str) -> User:
    """Récupère un utilisateur par son UUID."""
    return User.objects.filter(id=user_id, is_active=True).first()


def get_user_active_role(*, user: User):
    """Récupère le rôle actif d'un utilisateur dans son organisation."""
    return UserOrganizationRole.objects.filter(user=user, is_active=True).select_related('organization').first()