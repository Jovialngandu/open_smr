
import pytest
from unittest.mock import patch

from api.models import IsoControl
from services.search.engines.bm25 import (
    BM25SearchEngine,)
from  services.search.engines.hybrid import (
	HybridSearchEngine,)




@pytest.fixture
def backup_control(db):
    return IsoControl.objects.create(
        code="TEST.BACKUP",
        title="Sauvegarde des informations",
        theme="TECHNOLOGICAL",
        description=(
            "Des copies de sauvegarde doivent être effectuées "
            "et testées régulièrement."
        ),
        keywords=(
            "ransomware rançongiciel perte de données "
            "panne serveur crash restauration restaurer"
        ),
    )


@pytest.fixture
def vulnerability_control(db):
    return IsoControl.objects.create(
        code="TEST.VULN",
        title="Gestion des vulnérabilités techniques",
        theme="TECHNOLOGICAL",
        description=(
            "Les vulnérabilités techniques doivent être "
            "identifiées et traitées."
        ),
        keywords="failles correctifs mises à jour logiciels",
    )


@pytest.mark.django_db
def test_bm25_finds_control_through_keywords(
    backup_control, vulnerability_control
):
    results = BM25SearchEngine().search(
        "Que faire contre un ransomware et la perte de données ?",
        top_k=2,
    )

    assert results
    assert results[0].code == backup_control.code
    assert results[0].score_type == "bm25"


@pytest.mark.django_db
def test_bm25_returns_empty_for_unmatched_query(
    backup_control, vulnerability_control
):
    results = BM25SearchEngine().search(
        "zqxv qzxv plmrt",
        top_k=5,
    )

    assert results == []


@pytest.mark.django_db
def test_hybrid_fuses_vector_and_bm25_results(
    backup_control, vulnerability_control
):
    # Simule le classement vectoriel pour tester la fusion sans
    # dépendre du modèle ONNX pendant ce test.
    with patch(
        "services.search.engines.vector.VectorSearchEngine.search",
        return_value=[vulnerability_control, backup_control],
    ):
        results = HybridSearchEngine().search(
            "ransomware restauration perte de données",
            top_k=2,
        )

    assert len(results) == 2
    assert all(result.score_type == "rrf" for result in results)
    assert all(result.search_score > 0 for result in results)