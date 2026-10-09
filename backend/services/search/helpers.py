import unicodedata
import re
from api.models import IsoControl

def tokenize(text: str) -> list[str]:
    """Tokenisation simple, adaptée à une première version française."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    return re.findall(r"[a-z0-9]+", text)


def control_search_text(control: IsoControl) -> str:
    """Texte indexé par les moteurs lexicaux."""
    return " ".join(
        part for part in (
            control.code,
            control.title,
            control.description,
            control.keywords or "",
        )
        if part
    )


def annotate_result(control, score: float, score_type: str):
    """Ajoute un score de recherche sans modifier le modèle Django."""
    control.search_score = float(score)
    control.score_type = score_type
    return control
