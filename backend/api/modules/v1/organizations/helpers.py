import uuid
from django.utils.text import slugify
from api.models import Organization


def generate_unique_org_code(name: str) -> str:
    """Génère un code d'organisation unique et lisible (ex: ACME-A1B2)."""
    base_slug = slugify(name).upper().replace('-', '')[:6] or "ORG"

    while True:
        suffix = uuid.uuid4().hex[:4].upper()
        code = f"{base_slug}-{suffix}"
        if not Organization.objects.filter(code=code).exists():
            return code