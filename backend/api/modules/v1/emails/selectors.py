# selectors.py
from typing import Optional
from django.db.models import QuerySet
from api.models import EmailLog



def email_log_get(log_id: int) -> Optional[EmailLog]:
    return EmailLog.objects.filter(id=log_id).first()


def email_log_list(*, user_id: Optional[int] = None, organization_id: Optional[int] = None, email_type: Optional[str] = None) -> QuerySet[EmailLog]:
    queryset = EmailLog.objects.all()
    
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    if organization_id:
        queryset = queryset.filter(organization_id=organization_id)
    if email_type:
        queryset = queryset.filter(email_type=email_type)
        
    return queryset.select_related('user', 'organization')