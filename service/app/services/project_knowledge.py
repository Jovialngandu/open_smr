OPENSMR_REFERENCE_CONTEXT = """
Faits confirmés :
- OpenSMR est un projet de gestion des risques de sécurité de l'information conforme à la norme ISO/IEC 27001:2022.
- Le dépôt contient un backend Django REST Framework avec des modèles de risques, actifs, contrôles ISO, tâches, preuves et déclarations d'applicabilité.
- Le frontend du dépôt est une application Angular 21 ; le README du projet décrit une architecture Web découpée en backend Django et frontend Angular.
- Le backend expose une API REST versionnée sous /api/v1/ et utilise JWT, permissions RBAC et contexte multi-organisation / multi-périmètre.
- Le projet introduit des modules pour les actifs, le registre des risques, le plan de traitement, la déclaration d'applicabilité (SoA), les contrôles ISO et l'export de conformité.
- La logique de risque métier est calculée côté backend et repose sur les critères de vraisemblance et d'impact, sans modification de cette mission.
- Le projet distingue explicitement la couche Django/DRF (authentification, permissions, persistance, données métier) et la couche FastAPI (orchestration IA et génération de réponses).
- Le backend et le service IA communiquent via une clé de service interne et un contrat JSON dédié, sans exposer de secrets côté navigateur.
- Sentinel est un copilote IA d'OpenSMR : il aide à répondre aux questions autour du projet, de son architecture et de ses fonctionnalités, sans exécuter d'actions métier directes.
- Les fonctionnalités futures comme les actions métier, les outils d'exécution, le RAG ou les tâches asynchrones ne sont pas confirmées comme disponibles dans le dépôt actuel.

Inconnus :
- L'équipe de développement n'est pas confirmée comme une information utilisateur fiable dans le code et la documentation du dépôt ; elle ne doit pas être présentée comme connue sans source explicite.
- Les décideurs, la gouvernance interne, les clients finaux ou les statuts juridiques du projet ne sont pas confirmés dans le dépôt.
- Les détails d'un fournisseur IA particulier, de la stratégie de confidentialité ou de l'activité opérationnelle réelle en production ne sont pas garantis par le dépôt dans cette fiche.

Règles de réponse :
- Répondre à partir des faits confirmés de ce contexte et du message utilisateur.
- S'il manque une information fiable, le dire clairement sans la supposer.
- Séparer les fonctionnalités existantes, celles en cours de développement et celles uniquement envisagées.
- Éviter de répondre comme si les fonctionnalités non confirmées existaient déjà.
- Ne pas affirmer avoir consulté la base de données ou exécuté une opération sans preuve explicite.
"""
