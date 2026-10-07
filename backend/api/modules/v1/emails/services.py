# api/modules/v1/emails/services.py
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from api.models import EmailLog

def send_email(
    *,
    recipient_email: str,
    subject: str,
    template_name: str,
    context: dict,
    email_type: str,
    user=None,
    organization=None
) -> bool:
    """
    Fonction générique d'envoi d'e-mail avec rendu de template HTML,
    fallback texte brut et journalisation (EmailLog).
    """
    html_message = render_to_string(f'emails/{template_name}', context)
    plain_message = strip_tags(html_message)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@opensmr.com')

    try:
        success = send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        status = bool(success)
        error_msg = None
    except Exception as e:
        status = False
        error_msg = str(e)
        print(f"Erreur lors de l'envoi de l'e-mail à {recipient_email}: {error_msg}")

    EmailLog.objects.create(
        user=user,
        organization=organization,
        email_type=email_type,
        recipient=recipient_email,
        subject=subject,
        status=status,
        error_message=error_msg,
    )
    return status

def send_overdue_task_email(user, task) -> bool:
    """Envoie une alerte pour une tâche dont la due_date est dépassée."""
    context = {
        'username': user.username or user.first_name,
        'task_title': task.title,
        'due_date': task.due_date.strftime("%d/%m/%Y") if hasattr(task.due_date, 'strftime') else str(task.due_date),
        'task_url': f"{settings.FRONTEND_URL}/tasks/{task.id}",
    }
    return send_email(
        recipient_email=user.email,  # ✅ E-mail dynamique du destinataire
        subject=f"[Alerte Retard] La tâche '{task.title}' a dépassé son échéance",
        template_name="overdue_task_email.html",
        context=context,
        email_type=EmailLog.EmailType.OVERDUE_TASK_ALERT,
        user=user,
        organization=getattr(task, 'organization', None)
    )