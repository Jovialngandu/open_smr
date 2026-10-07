from django.core.mail.backends.base import BaseEmailBackend
from .brevo import BrevoProvider 

class ProviderEmailBackend(BaseEmailBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provider = BrevoProvider()

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        num_sent = 0
        for email_message in email_messages:
            if not email_message.recipients():
                continue

            mime_message = email_message.message()
            
            html_content = ""
            text_content = email_message.body

            if mime_message.is_multipart():
                for part in mime_message.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/html":
                        html_content = part.get_payload(decode=True).decode(
                            part.get_content_charset() or 'utf-8'
                        )
            else:
                if mime_message.get_content_type() == "text/html":
                    html_content = email_message.body

            if not html_content:
                html_content = email_message.body

            success = self.provider.send(
                subject=email_message.subject,
                body_html=html_content,
                body_text=text_content,
                from_email=email_message.from_email,
                recipient_list=email_message.recipients()
            )
            
            if success:
                num_sent += 1
                
        return num_sent