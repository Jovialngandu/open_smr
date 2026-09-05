from django.conf import settings
from django.db import models
from api.models.base import TimeStampedUUIDModel


class Organization(TimeStampedUUIDModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Scope(TimeStampedUUIDModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='scopes')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('organization', 'name')

    def __str__(self):
        return f"{self.organization.name} - {self.name}"


class UserOrganizationRole(TimeStampedUUIDModel):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('RSSI', 'RSSI'),
        ('RISK_OWNER', 'Propriétaire des Risques'),
        ('AUDITOR', 'Auditeur'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='org_roles')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='user_roles')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'organization', 'role')


class UserScopeAccess(TimeStampedUUIDModel):
    user_organization_role = models.ForeignKey(
        UserOrganizationRole, on_delete=models.CASCADE, related_name='scope_accesses'
    )
    scope = models.ForeignKey(Scope, on_delete=models.CASCADE, related_name='user_accesses')
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='granted_scope_accesses'
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_organization_role', 'scope')