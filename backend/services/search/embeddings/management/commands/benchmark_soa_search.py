
import json
import statistics
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.test import override_settings

from api.models import IsoControl
from backend.services.search.selectors import search_soa_controls


# Jugements initiaux de pertinence :
# 3 = très pertinent, 2 = pertinent, 1 = secondaire.
# À valider puis à enrichir avec des scénarios métier réels.
BENCHMARK_CASES = [
    # --- THÈME 1 : RH & GESTION DES ACCÈS (PEOPLE / ACCESS CONTROL) ---
    {
        "id": "employee_departure_access",
        "query": "Un employé quitte l'entreprise mais conserve encore l'accès aux systèmes internes.",
        "relevance": {"A.5.18": 3, "A.6.5": 3, "A.8.3": 2, "A.5.17": 1},
    },
    {
        "id": "dismissed_employee_login",
        "query": "Un ancien salarié peut toujours se connecter après son licenciement.",
        "relevance": {"A.5.18": 3, "A.6.5": 3, "A.5.17": 2, "A.8.3": 2},
    },
    {
        "id": "role_change_permissions",
        "query": "Un collaborateur change de poste et conserve des permissions qui ne sont plus nécessaires.",
        "relevance": {"A.5.18": 3, "A.8.3": 2, "A.8.32": 1},
    },
    {
        "id": "depart_with_company_secrets",
        "query": "Un employé part chez la concurrence avec les secrets commerciaux et les fichiers clients.",
        "relevance": {"A.6.6": 3, "A.6.5": 3, "A.8.12": 2, "A.5.12": 1},
    },
    {
        "id": "phishing_click_incident",
        "query": "Un salarié a cliqué sur un lien piège dans un mail douteux et a piégé son poste.",
        "relevance": {"A.6.3": 3, "A.6.8": 2, "A.8.7": 2, "A.5.26": 1},
    },
    {
        "id": "password_sharing",
        "query": "Plusieurs salariés partagent le même compte de messagerie et utilisent un mot de passe commun.",
        "relevance": {"A.5.17": 3, "A.5.18": 3, "A.8.3": 2, "A.6.5": 2},
    },
    {
        "id": "inactive_admin_account",
        "query": "Un compte administrateur n'a pas été désactivé après un départ de service et reste actif.",
        "relevance": {"A.5.17": 3, "A.8.3": 3, "A.5.18": 2, "A.8.32": 1},
    },
    {
        "id": "lost_company_laptop",
        "query": "Un ordinateur portable d'employé contenant des données clients a été perdu en déplacement.",
        "relevance": {"A.5.10": 3, "A.8.3": 3, "A.8.24": 2, "A.6.6": 1},
    },
    {
        "id": "contractor_access_expired",
        "query": "Un prestataire externe conserve encore des accès réseau après la fin du contrat.",
        "relevance": {"A.5.18": 3, "A.5.17": 3, "A.8.3": 2, "A.6.5": 2},
    },
    {
        "id": "shared_credentials",
        "query": "Le compte du responsable achat est utilisé par plusieurs personnes avec le même identifiant.",
        "relevance": {"A.5.17": 3, "A.6.5": 3, "A.8.3": 2, "A.5.18": 1},
    },

    # --- THÈME 2 : CYBERATTAQUES, INCIDENTS & APPLICATIONS (TECHNOLOGICAL & OPS) ---
    {
        "id": "ransomware_infection",
        "query": "Tous nos fichiers ont été chiffrés par un rançongiciel et le pirate demande une rançon.",
        "relevance": {"A.8.13": 3, "A.8.7": 3, "A.5.26": 2, "A.5.24": 1},
    },
    {
        "id": "unpatched_vulnerability_exploit",
        "query": "Des pirates ont exploité une faille de sécurité connue sur un serveur pas mis à jour.",
        "relevance": {"A.8.8": 3, "A.8.9": 2, "A.8.16": 1},
    },
    {
        "id": "data_leak_usb_exfiltration",
        "query": "Un commercial télécharge toute la base de données clients sur une clé USB personnelle.",
        "relevance": {"A.8.12": 3, "A.7.10": 2, "A.5.10": 2, "A.8.3": 1},
    },
    {
        "id": "web_application_sql_injection",
        "query": "Une faille dans le code source de l'application permet d'injecter du code malveillant sur le site web.",
        "relevance": {"A.8.28": 3, "A.8.25": 2, "A.8.29": 2, "A.8.26": 1},
    },
    {
        "id": "ddos_attack",
        "query": "Une attaque de déni de service paralyse le site web pendant plusieurs heures et bloque les ventes.",
        "relevance": {"A.8.22": 3, "A.8.23": 2, "A.5.26": 2, "A.8.31": 1},
    },
    {
        "id": "credential_stuffing",
        "query": "Des milliers de connexions frauduleuses sont tentées avec des identifiants volés sur le portail client.",
        "relevance": {"A.8.3": 3, "A.6.5": 2, "A.5.17": 2, "A.8.7": 1},
    },
    {
        "id": "api_key_leak_in_repo",
        "query": "Une clé API publique est détectée dans un dépôt Git non protégé et utilisée par des tiers.",
        "relevance": {"A.8.25": 3, "A.8.26": 2, "A.5.10": 2, "A.6.3": 1},
    },
    {
        "id": "malware_on_shared_drive",
        "query": "Un logiciel malveillant est détecté sur un disque partagé d'équipe et plusieurs ordinateurs sont infectés.",
        "relevance": {"A.8.7": 3, "A.8.9": 2, "A.5.26": 2, "A.6.3": 1},
    },
    {
        "id": "malicious_dependency_injection",
        "query": "Une dépendance logicielle tiers malveillante a été ajoutée au projet et exfiltre des secrets de build.",
        "relevance": {"A.8.25": 3, "A.8.26": 2, "A.8.31": 2, "A.6.3": 1},
    },
    {
        "id": "zero_day_firewall_exploit",
        "query": "Une vulnérabilité zéro jour sur le pare-feu permet à un attaquant d'accéder au réseau interne.",
        "relevance": {"A.8.8": 3, "A.8.16": 2, "A.8.21": 2, "A.5.26": 1},
    },

    # --- THÈME 3 : SÉCURITÉ PHYSIQUE & ENVIRONNEMENTALE (PHYSICAL) ---
    {
        "id": "unauthorized_building_tailgating",
        "query": "Un inconnu s'est glissé derrière un employé pour entrer dans les bureaux sans badge.",
        "relevance": {"A.7.2": 3, "A.7.1": 2, "A.7.4": 2},
    },
    {
        "id": "unlocked_server_room_theft",
        "query": "La salle des serveurs est restée ouverte et un équipement réseau a été volé la nuit.",
        "relevance": {"A.7.3": 3, "A.7.8": 2, "A.7.4": 2, "A.5.9": 1},
    },
    {
        "id": "visitor_badge_proxied_entry",
        "query": "Un visiteur utilise le badge d'un autre employé pour accéder au site sans autorisation.",
        "relevance": {"A.7.2": 3, "A.7.1": 2, "A.5.18": 2, "A.8.3": 1},
    },
    {
        "id": "printer_documents_left_unattended",
        "query": "Des documents confidentiels sont abandonnés sur une imprimante partagée et récupérés par un tiers.",
        "relevance": {"A.7.5": 3, "A.5.10": 2, "A.6.6": 2, "A.8.12": 1},
    },
    {
        "id": "server_room_cctv_gap",
        "query": "La salle serveur n'a pas de vidéosurveillance fiable et des accès non autorisés passent inaperçus.",
        "relevance": {"A.7.2": 3, "A.7.3": 2, "A.7.4": 2, "A.5.26": 1},
    },
    {
        "id": "loading_dock_unsecured",
        "query": "Le quai de livraison est ouvert sans contrôle et des colis contenant du matériel sensible sont volés.",
        "relevance": {"A.7.3": 3, "A.7.8": 2, "A.7.4": 2, "A.5.9": 1},
    },
    {
        "id": "backup_tape_disposal_risk",
        "query": "Des supports de sauvegarde contenant des données clients sont jetés sans destruction sécurisée.",
        "relevance": {"A.7.10": 3, "A.5.10": 2, "A.8.12": 2, "A.6.6": 1},
    },
    {
        "id": "office_equipment_theft",
        "query": "Des postes et des écrans sont volés pendant la nuit dans le bureau sans alarme activée.",
        "relevance": {"A.7.3": 3, "A.7.4": 2, "A.7.2": 2, "A.5.9": 1},
    },
    {
        "id": "datacenter_power_outage",
        "query": "Coupure de courant soudaine dans la salle serveur et panne de l'alimentation électrique.",
        "relevance": {"A.7.11": 3, "A.5.30": 2, "A.8.14": 2},
    },
    {
        "id": "server_room_open_after_hours",
        "query": "La salle des serveurs reste ouverte en dehors des heures de travail et personne ne contrôle l'accès.",
        "relevance": {"A.7.3": 3, "A.7.2": 2, "A.7.4": 2, "A.5.18": 1},
    },

    # # --- THÈME 4 : FOURNISSEURS, CLOUD & RGPD (ORGANIZATIONAL / THIRD PARTY) ---
    {
        "id": "cloud_provider_data_breach",
        "query": "Piratage des données hébergées chez notre prestataire Cloud externe.",
        "relevance": {"A.5.23": 3, "A.5.19": 3, "A.5.20": 2, "A.5.24": 1},
    },
    {
        "id": "personal_data_gdpr_leak",
        "query": "Fuite de données à caractère personnel et risque d'amende lourde du régulateur.",
        "relevance": {"A.5.34": 3, "A.5.5": 2, "A.5.31": 2, "A.5.24": 1},
    },
    {
        "id": "supplier_access_without_review",
        "query": "Un fournisseur a accès à nos systèmes de production sans revue régulière de ses droits.",
        "relevance": {"A.5.23": 3, "A.5.19": 3, "A.5.18": 2, "A.6.5": 1},
    },
    {
        "id": "insecure_file_sharing_saas",
        "query": "Des fichiers clients sont partagés via un outil SaaS non approuvé et sans contrôle d'accès.",
        "relevance": {"A.5.23": 3, "A.5.20": 2, "A.5.10": 2, "A.8.3": 1},
    },
    {
        "id": "data_retention_violation",
        "query": "Des données personnelles sont conservées bien au-delà de la durée légale et peuvent être retrouvées en archive.",
        "relevance": {"A.5.33": 3, "A.5.34": 2, "A.5.31": 2, "A.6.6": 1},
    },
    {
        "id": "cross_border_transfer_gap",
        "query": "Des données sont transférées hors de l'Union européenne sans vérification des garanties contractuelles.",
        "relevance": {"A.5.34": 3, "A.5.31": 2, "A.5.20": 2, "A.5.24": 1},
    },
    {
        "id": "vendor_admin_account_exposure",
        "query": "Un compte administrateur du prestataire a été compromis et a accès à plusieurs environnements client.",
        "relevance": {"A.5.19": 3, "A.5.23": 3, "A.5.18": 2, "A.8.3": 1},
    },
    {
        "id": "subcontractor_data_transfer",
        "query": "Un sous-traitant de notre fournisseur reçoit des données sensibles sans accord de sécurité formalisé.",
        "relevance": {"A.5.23": 3, "A.5.20": 3, "A.5.31": 2, "A.5.24": 1},
    },
    {
        "id": "security_questionnaire_stale",
        "query": "Le fournisseur n'a pas mis à jour ses contrôles de sécurité depuis deux ans et maintient des vulnérabilités connues.",
        "relevance": {"A.5.23": 3, "A.5.19": 2, "A.5.20": 2, "A.8.8": 1},
    },
    {
        "id": "customer_contract_data_exposure",
        "query": "Des contrats clients et des données commerciales sont exposés dans un espace partagé externe sans protection suffisante.",
        "relevance": {"A.5.10": 3, "A.5.23": 2, "A.6.6": 2, "A.8.3": 1},
    },

    # # --- THÈME 5 : CONTINUITÉ, RÉPONSE AUX INCIDENTS & EXPLOITATION (RESILIENCE / OPERATIONS) ---
    {
        "id": "untested_prod_deployment_crash",
        "query": "Un développeur a fait une mise à jour directement en production un vendredi soir et a fait planter le site.",
        "relevance": {"A.8.32": 3, "A.8.31": 3, "A.8.25": 1},
    },
    {
        "id": "backup_restore_test_failure",
        "query": "La base de données ne peut pas être restaurée depuis les sauvegardes lors d'un test de reprise d'activité.",
        "relevance": {"A.8.13": 3, "A.8.32": 2, "A.5.30": 2, "A.8.31": 1},
    },
    {
        "id": "database_outage_due_to_config",
        "query": "Une mauvaise configuration de la base de données provoque une panne qui bloque les transactions critiques.",
        "relevance": {"A.8.31": 3, "A.8.32": 2, "A.8.25": 2, "A.5.26": 1},
    },
    {
        "id": "dns_hijack",
        "query": "Le DNS de l'entreprise a été détourné et les utilisateurs sont redirigés vers un site frauduleux.",
        "relevance": {"A.8.21": 3, "A.8.24": 2, "A.8.7": 2, "A.5.26": 1},
    },
    {
        "id": "incident_response_delay",
        "query": "Un incident de sécurité est détecté trop tard et la réponse n'est déclenchée qu'après plusieurs heures.",
        "relevance": {"A.5.26": 3, "A.6.8": 2, "A.8.7": 2, "A.8.31": 1},
    },
    {
        "id": "monitoring_alerts_missing",
        "query": "Aucune alerte n'est déclenchée lors d'une tentative de connexion anormale sur les serveurs critiques.",
        "relevance": {"A.5.26": 3, "A.8.7": 2, "A.8.31": 2, "A.6.8": 1},
    },
    {
        "id": "security_patch_deployment_lag",
        "query": "Les correctifs de sécurité sont appliqués trop tard et une vulnérabilité connue persiste sur les serveurs.",
        "relevance": {"A.8.8": 3, "A.8.9": 2, "A.8.31": 2, "A.5.26": 1},
    },
    {
        "id": "code_signing_bypass",
        "query": "Un script non signé est exécuté en production lors d'un déploiement manqué, sans contrôle de signature.",
        "relevance": {"A.8.25": 3, "A.8.31": 2, "A.8.26": 2, "A.5.26": 1},
    },
    {
        "id": "production_database_exposed",
        "query": "Une base de production est accessible publiquement à partir d'un port non protégé sur internet.",
        "relevance": {"A.8.3": 3, "A.8.21": 2, "A.8.24": 2, "A.5.26": 1},
    },
    {
        "id": "api_bruteforce_attack",
        "query": "Des attaques par force brute ciblent les points d'entrée API et saturent les services transactionnels.",
        "relevance": {"A.8.3": 3, "A.8.22": 2, "A.8.7": 2, "A.5.26": 1},
    },
]

ENGINES = ("vector", "bm25", "hybrid")
TOP_K = 5

DIAGNOSTIC_QUERIES = {
    "empty": "",
    "unknown_terms": "qzxv plmrt zqxv 918273",
}


def dcg(grades):
    """Discounted cumulative gain."""
    return sum(
        (2**grade - 1) / __import__("math").log2(rank + 1)
        for rank, grade in enumerate(grades, start=1)
    )


def evaluate_ranking(result_codes, relevance, k=TOP_K):
    """Calcule les métriques à partir des jugements de pertinence."""
    ranked = list(result_codes[:k])
    relevant_codes = {
        code for code, grade in relevance.items() if grade > 0
    }

    hits = sum(code in relevant_codes for code in ranked)

    precision = hits / k if k else 0.0
    recall = (
        hits / len(relevant_codes)
        if relevant_codes
        else 0.0
    )

    reciprocal_rank = 0.0
    for rank, code in enumerate(ranked, start=1):
        if code in relevant_codes:
            reciprocal_rank = 1 / rank
            break

    actual_grades = [
        relevance.get(code, 0) for code in ranked
    ]
    ideal_grades = sorted(
        relevance.values(), reverse=True
    )[:k]

    ideal_dcg = dcg(ideal_grades)
    ndcg = dcg(actual_grades) / ideal_dcg if ideal_dcg else 0.0

    return {
        "precision_at_5": round(precision, 4),
        "recall_at_5": round(recall, 4),
        "mrr": round(reciprocal_rank, 4),
        "ndcg_at_5": round(ndcg, 4),
    }


class Command(BaseCommand):
    help = (
        "Compare automatiquement les moteurs de recherche "
        "SoA vector, BM25 et hybride."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="/tmp/soa_search_benchmark.json",
            help="Chemin du rapport JSON.",
        )
        parser.add_argument(
            "--top-k",
            type=int,
            default=TOP_K,
            help="Nombre de résultats à évaluer.",
        )
        parser.add_argument(
            "--repeats",
            type=int,
            default=3,
            help="Nombre de répétitions pour mesurer la latence.",
        )

    def handle(self, *args, **options):
        top_k = options["top_k"]
        repeats = options["repeats"]

        if top_k < 1 or repeats < 1:
            self.stderr.write(
                self.style.ERROR(
                    "--top-k et --repeats doivent être >= 1."
                )
            )
            return

        existing_codes = set(
            IsoControl.objects.values_list("code", flat=True)
        )

        missing_codes = sorted({
            code
            for case in BENCHMARK_CASES
            for code in case["relevance"]
            if code not in existing_codes
        })

        if not existing_codes:
            self.stderr.write(
                self.style.ERROR(
                    "Aucun contrôle ISO trouvé en base."
                )
            )
            return

        if missing_codes:
            self.stderr.write(
                self.style.WARNING(
                    "Contrôles de référence absents de la base : "
                    + ", ".join(missing_codes)
                )
            )

        original_engine = getattr(
            settings, "SOA_SEARCH_ENGINE", "vector"
        )

        report = {
            "metadata": {
                "engines": list(ENGINES),
                "top_k": top_k,
                "repeats": repeats,
                "database_control_count": len(existing_codes),
                "missing_reference_codes": missing_codes,
                "embedding_engine": getattr(
                    settings, "EMBEDDING_ENGINE", None
                ),
                "original_search_engine": original_engine,
                "warning": (
                    "Les métriques dépendent des jugements de "
                    "pertinence déclarés dans BENCHMARK_CASES."
                ),
            },
            "engines": {},
            "diagnostics": {},
        }

        for engine in ENGINES:
            engine_cases = []
            metric_values = {
                "precision_at_5": [],
                "recall_at_5": [],
                "mrr": [],
                "ndcg_at_5": [],
            }

            self.stdout.write(f"\nÉvaluation : {engine}")

            with override_settings(SOA_SEARCH_ENGINE=engine):
                for case in BENCHMARK_CASES:
                    durations = []
                    controls = []
                    error = None

                    for _ in range(repeats):
                        started = time.perf_counter()

                        try:
                            controls = list(
                                search_soa_controls(
                                    case["query"], top_k=top_k
                                )
                            )
                        except Exception as exc:
                            error = (
                                f"{type(exc).__name__}: {exc}"
                            )
                            break

                        durations.append(
                            (time.perf_counter() - started) * 1000
                        )

                    result_codes = [
                        control.code for control in controls
                    ]

                    metrics = (
                        evaluate_ranking(
                            result_codes,
                            case["relevance"],
                            k=top_k,
                        )
                        if error is None
                        else None
                    )

                    if metrics:
                        for key, value in metrics.items():
                            metric_values[key].append(value)

                    results = [
                        {
                            "code": control.code,
                            "title": control.title,
                            "score": getattr(
                                control, "search_score", None
                            ),
                            "score_type": getattr(
                                control, "score_type", None
                            ),
                        }
                        for control in controls
                    ]

                    entry = {
                        "id": case["id"],
                        "query": case["query"],
                        "expected_relevance": case["relevance"],
                        "results": results,
                        "metrics": metrics,
                        "latency_ms_median": (
                            round(statistics.median(durations), 2)
                            if durations
                            else None
                        ),
                        "error": error,
                    }

                    engine_cases.append(entry)

                    status = (
                        f"MRR={metrics['mrr']:.3f}, "
                        f"nDCG@{top_k}="
                        f"{metrics['ndcg_at_5']:.3f}"
                        if metrics
                        else f"ERREUR: {error}"
                    )

                    self.stdout.write(
                        f"  {case['id']}: {status}"
                    )

            averages = {}
            for key, values in metric_values.items():
                averages[key] = (
                    round(statistics.mean(values), 4)
                    if values
                    else None
                )

            latencies = [
                case["latency_ms_median"]
                for case in engine_cases
                if case["latency_ms_median"] is not None
            ]

            report["engines"][engine] = {
                "macro_average_metrics": averages,
                "median_query_latency_ms": (
                    round(statistics.median(latencies), 2)
                    if latencies
                    else None
                ),
                "cases": engine_cases,
            }

            # Tests diagnostiques : ils ne sont pas inclus dans
            # les métriques de pertinence.
            diagnostic_results = {}

            with override_settings(SOA_SEARCH_ENGINE=engine):
                for name, query in DIAGNOSTIC_QUERIES.items():
                    started = time.perf_counter()
                    error = None

                    try:
                        controls = list(
                            search_soa_controls(query, top_k=top_k)
                        )
                    except Exception as exc:
                        controls = []
                        error = f"{type(exc).__name__}: {exc}"

                    diagnostic_results[name] = {
                        "query": query,
                        "returned_count": len(controls),
                        "returned_codes": [
                            control.code for control in controls
                        ],
                        "latency_ms": round(
                            (time.perf_counter() - started) * 1000,
                            2,
                        ),
                        "error": error,
                    }

            report["diagnostics"][engine] = diagnostic_results

        output_path = Path(options["output"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nRapport enregistré dans : {output_path}"
            )
        )

        self.stdout.write("\nComparaison synthétique")
        for engine, data in report["engines"].items():
            metrics = data["macro_average_metrics"]
            self.stdout.write(
                f"{engine:>8} | "
                f"MRR={metrics['mrr']} | "
                f"nDCG@{top_k}={metrics['ndcg_at_5']} | "
                f"latence médiane="
                f"{data['median_query_latency_ms']} ms"
            )