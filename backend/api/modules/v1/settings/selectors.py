from typing import Optional
from django.contrib.auth import get_user_model
from api.models.support import UserPreference, SystemSetting

User = get_user_model()


def get_user_preferences(*, user: User) -> UserPreference:
    """Récupère les préférences d'un utilisateur, les crée par défaut si elles n'existent pas."""
    preference, _ = UserPreference.objects.get_or_create(user=user)
    return preference


def get_system_setting_by_key(*, key: str) -> Optional[SystemSetting]:
    """Récupère un paramètre système par sa clé unique."""
    try:
        return SystemSetting.objects.get(key=key)
    except SystemSetting.DoesNotExist:
        return None


def list_system_settings():
    """Liste tous les paramètres système."""
    return SystemSetting.objects.all().order_by('key')