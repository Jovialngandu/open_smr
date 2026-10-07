# models.py
from django.db import models
from django.conf import settings
from api.models.organization import Organization
from api.models.base import TimeStampedUUIDModel

class EmailLog(TimeStampedUUIDModel):
    class EmailType(models.TextChoices):
        # Authentification & Comptes
        MFA_CODE = 'MFA_CODE', 'Code MFA'
        WELCOME = 'WELCOME', 'Bienvenue'
        RECOVERY = 'RECOVERY', 'Récupération'
        INVITATION = 'INVITATION', 'Invitation Organisation'
        
        # Open SMR / Risques & Tâches
        OVERDUE_TASK_ALERT = 'OVERDUE_TASK_ALERT', 'Alerte Tâche en Retard'
        RISK_NOTIFICATION = 'RISK_NOTIFICATION', 'Notification de Risque'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='email_logs',
        null=True, blank=True
    )
    # Optionnel : lier l'email à une organisation spécifique
    organization = models.ForeignKey(Organization,on_delete=models.SET_NULL,null=True, blank=True,related_name='email_logs')
    email_type = models.CharField(max_length=50, choices=EmailType.choices)
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True) 


    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['user', 'email_type']),
            models.Index(fields=['organization']),
        ]

    def __str__(self):
        return f"{self.email_type} à {self.recipient} le {self.sent_at.strftime('%Y-%m-%d %H:%M')}"