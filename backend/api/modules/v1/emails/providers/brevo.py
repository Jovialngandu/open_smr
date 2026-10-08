import requests
import os
from .base import EmailProvider

class BrevoProvider(EmailProvider):
    def __init__(self):
        self.url = os.getenv('BREVO_URL', 'https://api.brevo.com/v3/smtp/email')
        self.api_key = os.getenv('BREVO_API_KEY')

    def send(self, subject: str, body_html: str, body_text: str, from_email: str, recipient_list: list) -> bool:
        if not self.api_key:
            return False

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": self.api_key
        }
        
        payload = {
            "sender": {"email": from_email, "name": "OpenSMR"},
            "to": [{"email": email} for email in recipient_list],
            "subject": subject,
            "htmlContent": body_html,
            "textContent": body_text
        }
        
        try:
            response = requests.post(self.url, json=payload, headers=headers, timeout=10)
            # Brevo renvoie 201 en cas de succès
            return response.status_code == 201
        except Exception as e:
            return False
