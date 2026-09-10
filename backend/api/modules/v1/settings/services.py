from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound
from api.models.support  import UserPreference, SystemSetting
from api.modules.v1.settings.selectors import get_user_preferences

User = get_user_model()


def update_user_preferences(*, user: User, data: dict) -> UserPreference:
    """Met à jour partiellement ou totalement les préférences de l'utilisateur."""
    preference = get_user_preferences(user=user)

    fields = ['language', 'theme', 'timezone', 'email_notifications']
    updated_fields = []

    for field in fields:
        if field in data:
            setattr(preference, field, data[field])
            updated_fields.append(field)

    if updated_fields:
        preference.save(update_fields=updated_fields)

    return preference


def update_system_setting(*, key: str, value: dict | str | list | int | bool, description: str = None) -> SystemSetting:
    """Met à jour ou crée un paramètre système (clé/valeur)."""
    setting, created = SystemSetting.objects.get_or_create(
        key=key,
        defaults={'value': value, 'description': description}
    )

    if not created:
        setting.value = value
        updated_fields = ['value']
        if description is not None:
            setting.description = description
            updated_fields.append('description')
        setting.save(update_fields=updated_fields)

    return setting