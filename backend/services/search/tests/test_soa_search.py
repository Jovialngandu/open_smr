import pytest

from api.models import IsoControl
from services.search.selectors import get_embedding_provider
from services.search.selectors import search_soa_controls


@pytest.fixture
def iso_controls(db):
    provider = get_embedding_provider()

    controls = [
        {
            "code": "A.5.1",
            "title": "Politiques de sécurité de l'information",
            "theme": "ORGANIZATIONAL",
            "description": (
                "Les politiques de sécurité de l'information et les politiques "
                "spécifiques à chaque thème doivent être définies, approuvées "
                "par la direction, publiées, communiquées et portées à la "
                "connaissance du personnel concerné."
            ),
        },
        {
            "code": "A.5.2",
            "title": "Rôles et responsabilités liés à la sécurité de l'information",
            "theme": "ORGANIZATIONAL",
            "description": (
                "Les rôles et responsabilités liés à la sécurité de "
                "l'information doivent être définis et attribués conformément "
                "aux besoins de l'organisation."
            ),
        },
        {
            "code": "A.5.3",
            "title": "Séparation des devoirs",
            "theme": "ORGANIZATIONAL",
            "description": (
                "Les devoirs et les domaines de responsabilité conflictuels "
                "doivent être séparés afin de réduire les risques de "
                "modification non autorisée ou involontaire, ou de mauvaise "
                "utilisation des actifs de l'organisation."
            ),
        },
        {
            "code": "A.5.7",
            "title": "Renseignement sur les menaces",
            "theme": "ORGANIZATIONAL",
            "description": (
                "Des informations relatives aux menaces pesant sur la sécurité "
                "de l'information doivent être collectées et analysées pour "
                "produire des renseignements sur les menaces."
            ),
        },
        
        {
			"code": "A.8.2",
			"title": "Droits d'accès privilégiés",
			"theme": "TECHNOLOGICAL",
			"description": (
				"L'attribution et l'utilisation des droits d'accès privilégiés "
				"doivent être restreintes et gérées de manière stricte afin d'éviter "
				"les accès non autorisés et les abus de pouvoir."
			),
		},
        
        {
			"code": "A.8.18",
			"title": "Utilisation des programmes d'utilitaires privilégiés",
			"theme": "TECHNOLOGICAL",
			"description": (
				"L'utilisation de programmes utilitaires susceptibles de contourner "
				"les contrôles des systèmes et des applications doit être restreinte "
				"et contrôlée de manière stricte."
			),
		},
        {
			"code": "A.8.14",
			"title": "Gestion des modifications",
			"theme": "TECHNOLOGICAL",
			"description": (
				"Les modifications apportées aux installations de traitement de "
				"l'information et aux systèmes d'information doivent être contrôlées "
				"par un processus formel d'approbation et de suivi."
			),
		}
    ]

    created_controls = []

    for data in controls:
        text = (
            f"{data['code']} "
            f"{data['title']} "
            f"{data['description']}"
        )

        embedding = provider.get_embedding(text)

        control = IsoControl.objects.create(
            **data,
            embedding=embedding,
        )

        created_controls.append(control)

    return created_controls


def test_search_separation_of_duties(iso_controls):
    results = search_soa_controls(
        "Un administrateur possède plusieurs responsabilités "
        "qui devraient être séparées afin de réduire les conflits "
        "et les risques de modification non autorisée.",
        top_k=3,
    )

    codes = [control.code for control in results]

    assert "A.5.3" in codes


def test_search_security_policy(iso_controls):
    results = search_soa_controls(
        "L'organisation doit définir et communiquer "
        "ses politiques de sécurité de l'information au personnel.",
        top_k=3,
    )

    codes = [control.code for control in results]

    assert "A.5.1" in codes


def test_search_threat_intelligence(iso_controls):
    results = search_soa_controls(
        "L'organisation doit collecter et analyser "
        "des informations concernant les menaces de sécurité.",
        top_k=3,
    )

    codes = [control.code for control in results]

    assert "A.5.7" in codes