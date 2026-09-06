# 🛡️ OpenSMR — Backend API

Backend Django REST Framework pour la gestion du Système de Management de la Sécurité de l'Information (SMSI) conforme à la norme **ISO/IEC 27001:2022**.

Actuellement, l'application est en phase de définition de l'architecture des données et de mise en place des modèles ORM avec gestion du **Soft Delete (`deleted_at`)**.

---

## 🏗️ Structure Actuelle du Module `api`

Les modèles de données ont été structurés et découpés dans le dossier `api/models/` :

```text
backend/
├── api/
│   ├── apps.py              # Configuration de l'application API
│   ├── models/              # Modèles de données ORM
│   │   ├── __init__.py      # Export centralisé des modèles
│   │   ├── base.py          # TimeStampedUUIDModel, SoftDeleteQuerySet, SoftDeleteManager
│   │   ├── organization.py  # Organization, Scope, UserOrganizationRole, UserScopeAccess
│   │   ├── iso27001.py      # Asset, Risk, IsoControl, SoaEntry, TreatmentTask, Evidence, SoaVersion
│   │   └── support.py       # UserPreference, SystemSetting
├── core/                    # Configuration globale du projet Django
│   ├── settings.py          # Configuration INSTALLED_APPS, DATABASES, etc.
│   └── urls.py
└── manage.py
```

### 🗄️ Modèles de Données Mis en Place

#### 1. Socle Commun (`api/models/base.py`)
* **TimeStampedUUIDModel** : Modèle abstrait fournissant :
  * `id` : Clef primaire UUIDv4.
  * `created_at` / `updated_at` : Horodatages automatiques.
  * `deleted_at` : Champ pour le Soft Delete.
  * `objects` : Custom SoftDeleteManager filtrant automatiquement les éléments supprimés (`deleted_at__isnull=True`).
  * `all_objects` : Manager standard Django pour accéder à l'ensemble des données (y compris archivées).

#### 2. Organisation & Sécurité RBAC (`api/models/organization.py`)
* **Organization** : Entité juridique (champs `name`, `code`, `description`).
* **Scope** : Périmètre d'application ISO 27001 rattaché à une organisation.
* **UserOrganizationRole** : Rôle d'un utilisateur au sein d'une organisation (`ADMIN`, `RSSI`, `RISK_OWNER`, `AUDITOR`) avec statut `is_active` et date d'affiliation `joined_at`.
* **UserScopeAccess** : Accès granulaire d'un membre d'organisation à un périmètre (Scope) spécifique.

#### 3. Core ISO 27001 (`api/models/iso27001.py`)
* **Asset** : Patrimoine à protéger lié à un périmètre. Contient l'évaluation DIC (1 à 3) (`confidentiality`, `integrity`, `availability`).
* **Risk** : Scénarios d'incidents identifiés sur un actif (Vraisemblance 1-5, Impact 1-5, statut : `OPEN`, `IN_MITIGATION`, `ACCEPTED`, `CLOSED`).
* **IsoControl** : Catalogue global des 93 mesures ISO 27001:2022 réparties par thème (`ORGANIZATIONAL`, `PEOPLE`, `PHYSICAL`, `TECHNOLOGICAL`).
* **SoaEntry** : Déclaration d'applicabilité (SoA) liée à un périmètre et à une mesure (`NOT_IMPLEMENTED`, `IN_PROGRESS`, `IMPLEMENTED`).
* **TreatmentTask** : Plan de traitement des risques. La complétion d'une tâche met automatiquement à jour le statut du contrôle SoA correspondant.
* **Evidence** : Stockage des fichiers de preuves liées aux tâches de traitement.
* **SoaVersion** : Instantané (snapshot JSON) figé d'une SoA pour audit (`DRAFT`, `APPROVED`).

#### 4. Support & Configuration (`api/models/support.py`)
* **UserPreference** : Langue, thème (`LIGHT`, `DARK`, `SYSTEM`), fuseau horaire, notifications email.
* **SystemSetting** : Clef/valeur dynamique (stockage au format `JSONField`).

---

## 🚀 Initialisation & Exécution des Migrations

### 1. Activer l'environnement virtuel
```bash
cd backend
source venv/bin/activate
```

### 2. Configuration dans `core/settings.py`
S'assurer que l'application `api` est bien déclarée dans `INSTALLED_APPS` :
```python
INSTALLED_APPS = [
    # ...
    'api.apps.ApiConfig',
]
```

### 3. Génération et application des migrations
Exécuter la création du schéma de base de données à partir des modèles :
```bash
# Générer le fichier de migration initial pour l'application api
python manage.py makemigrations api

# Appliquer les migrations dans la base de données
python manage.py migrate
```

### 4. Lancer le serveur local
```bash
python manage.py runserver
```
