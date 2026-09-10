import uuid
from django.utils.text import slugify


def generate_unique_org_code(name: str) -> str:
    """Génère un code d'organisation lisible et unique (ex: ACME-A1B2)."""
    base_slug = slugify(name).upper().replace('-', '')[:6] or "ORG"
    suffix = uuid.uuid4().hex[:4].upper()
    return f"{base_slug}-{suffix}"