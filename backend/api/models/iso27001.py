from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from api.models.base import TimeStampedUUIDModel
from api.models.organization import Scope


class Asset(TimeStampedUUIDModel):
    CATEGORY_CHOICES = [
        ('HARDWARE', 'Matériel'),
        ('SOFTWARE', 'Logiciel'),
        ('DATA', 'Données'),
        ('PEOPLE', 'Ressources Humaines'),
        ('SERVICE', 'Service'),
    ]

    scope = models.ForeignKey(Scope, on_delete=models.CASCADE, related_name='assets')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='owned_assets'
    )
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, null=True)

    # Critères DIC (1 à 3)
    confidentiality = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)], default=1)
    integrity = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)], default=1)
    availability = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)], default=1)

    @property
    def criticality(self):
        return max(self.confidentiality, self.integrity, self.availability)

    def __str__(self):
        return f"{self.name} ({self.category})"


class Risk(TimeStampedUUIDModel):
    STATUS_CHOICES = [
        ('OPEN', 'Ouvert'),
        ('IN_MITIGATION', 'En Mitigeage'),
        ('ACCEPTED', 'Accepté'),
        ('CLOSED', 'Clôturé'),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='risks')
    code = models.CharField(max_length=50, db_index=True)
    threat_description = models.TextField()

    # Vraisemblance (1-5) & Impact (1-5)
    likelihood = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    impact = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='OPEN')

    @property
    def score(self):
        return self.likelihood * self.impact

    def __str__(self):
        return f"{self.code} - {self.asset.name}"


class IsoControl(TimeStampedUUIDModel):
    THEME_CHOICES = [
        ('ORGANIZATIONAL', 'Organisationnel'),
        ('PEOPLE', 'Humain'),
        ('PHYSICAL', 'Physique'),
        ('TECHNOLOGICAL', 'Technologique'),
    ]

    code = models.CharField(max_length=20, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    theme = models.CharField(max_length=50, choices=THEME_CHOICES)
    description = models.TextField()

    def __str__(self):
        return f"{self.code} - {self.title}"


class SoaEntry(TimeStampedUUIDModel):
    STATUS_CHOICES = [
        ('NOT_IMPLEMENTED', 'Non Implémenté'),
        ('IN_PROGRESS', 'En Cours'),
        ('IMPLEMENTED', 'Implémenté'),
    ]

    scope = models.ForeignKey(Scope, on_delete=models.CASCADE, related_name='soa_entries')
    iso_control = models.ForeignKey(IsoControl, on_delete=models.CASCADE, related_name='soa_entries')
    is_applicable = models.BooleanField(default=True)
    justification = models.TextField(blank=True, null=True)
    implementation_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='NOT_IMPLEMENTED')

    class Meta:
        unique_together = ('scope', 'iso_control')


class TreatmentTask(TimeStampedUUIDModel):
    STATUS_CHOICES = [
        ('TODO', 'À Faire'),
        ('IN_PROGRESS', 'En Cours'),
        ('COMPLETED', 'Terminé'),
    ]

    risk = models.ForeignKey(Risk, on_delete=models.CASCADE, related_name='treatment_tasks')
    iso_control = models.ForeignKey(IsoControl, on_delete=models.CASCADE, related_name='treatment_tasks')
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assigned_tasks'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='TODO')
    completed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Innovation : passage automatique du contrôle SoA à IMPLEMEMTED lors de la complétion
        if self.status == 'COMPLETED':
            scope = self.risk.asset.scope
            SoaEntry.objects.filter(scope=scope, iso_control=self.iso_control).update(
                implementation_status='IMPLEMENTED'
            )


class Evidence(TimeStampedUUIDModel):
    task = models.ForeignKey(TreatmentTask, on_delete=models.CASCADE, related_name='evidences')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    file_path = models.FileField(upload_to='evidences/%Y/%m/')
    description = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class SoaVersion(TimeStampedUUIDModel):
    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('APPROVED', 'Approuvé'),
    ]

    scope = models.ForeignKey(Scope, on_delete=models.CASCADE, related_name='soa_versions')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='approved_soa_versions'
    )
    version_number = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    snapshot_data = models.JSONField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='DRAFT')

    class Meta:
        unique_together = ('scope', 'version_number')