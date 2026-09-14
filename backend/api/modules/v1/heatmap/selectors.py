from typing import Dict, List, Any
from collections import defaultdict
from api.models.iso27001 import Risk


def get_risk_severity(score: int) -> str:
    """
    Détermine le niveau de sévérité basé sur le score de criticité (likelihood * impact).
    """
    if score >= 15:
        return 'HIGH'      # Rouge (15-25)
    elif score >= 8:
        return 'MEDIUM'    # Jaune / Orange (8-12)
    return 'LOW'           # Vert (1-6)


def get_heatmap_matrix_data(*, scope_id: str) -> Dict[str, Any]:
    """
    Calcule la matrice 5x5 des risques pour un scope avec détails enrichis (severity, liste des risques).
    """
    # Extraction des risques du périmètre
    risks_qs = Risk.objects.filter(asset__scope_id=scope_id).values(
        'id', 'code', 'threat_description', 'status', 'likelihood', 'impact'
    )

    # Dictionnaire regroupant les risques par tuple (likelihood, impact)
    grouped_risks = defaultdict(list)
    for risk in risks_qs:
        key = (risk['likelihood'], risk['impact'])
        grouped_risks[key].append({
            'id': risk['id'],
            'code': risk['code'],
            'threat_description': risk['threat_description'],
            'status': risk['status']
        })

    # Génération des 25 cellules (1..5 x 1..5)
    cells = []
    for likelihood in range(1, 6):
        for impact in range(1, 6):
            score = likelihood * impact
            cell_risks = grouped_risks.get((likelihood, impact), [])
            
            cells.append({
                'likelihood': likelihood,
                'impact': impact,
                'score': score,
                'severity': get_risk_severity(score),
                'count': len(cell_risks),
                'risks': cell_risks
            })

    return {
        'scope_id': scope_id,
        'total_risks': len(risks_qs),
        'matrix': cells
    }