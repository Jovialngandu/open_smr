from typing import Dict, List, Any
from django.db.models import Count
from api.models.iso27001 import Risk


def get_heatmap_matrix_data(*, scope_id: str) -> Dict[str, Any]:
    """
    Calcule la matrice 5x5 des risques pour un périmètre donné (scope_id).
    Retourne la liste des cellules avec le nombre de risques et le détail basique.
    """
    # Filtrer les risques par scope (via asset__scope_id)
    risks_qs = Risk.objects.filter(asset__scope_id=scope_id)

    # Agrégation des risques par (likelihood, impact)
    grouped = (
        risks_qs
        .values('likelihood', 'impact')
        .annotate(count=Count('id'))
    )

    # Map pour accès rapide (likelihood, impact) -> count
    counts_map = {
        (item['likelihood'], item['impact']): item['count']
        for item in grouped
    }

    # Génération de la grille complète 5x5 (likelihood: 1..5, impact: 1..5)
    cells = []
    for likelihood in range(1, 6):
        for impact in range(1, 6):
            criticity_score = likelihood * impact
            cells.append({
                'likelihood': likelihood,
                'impact': impact,
                'score': criticity_score,
                'count': counts_map.get((likelihood, impact), 0)
            })

    total_risks = risks_qs.count()

    return {
        'scope_id': scope_id,
        'total_risks': total_risks,
        'matrix': cells
    }