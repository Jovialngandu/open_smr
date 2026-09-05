from django.conf import settings
from django.db import models
from api.models.base import TimeStampedUUIDModel


class UserPreference(TimeStampedUUIDModel):
    THEME_CHOICES = [
        ('LIGHT', 'Clair'),
        ('DARK', 'Sombre'),
        ('SYSTEM', 'Système'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preference')
    language = models.CharField(max_length=10, default='fr')
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='LIGHT')
    timezone = models.CharField(max_length=50, default='Africa/Kinshasa')
    email_notifications = models.BooleanField(default=True)


class SystemSetting(TimeStampedUUIDModel):
    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.JSONField()  # Permet de stocker texte brut ou structures complexes
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.key