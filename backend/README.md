# 🛡️ OpenSMR — Backend API

Backend Django REST Framework pour la gestion du Système de Management de la Sécurité de l'Information (SMSI) conforme à la norme **ISO/IEC 27001:2022**.

Actuellement, l'application est en phase de définition de l'architecture des données, de mise en place des modèles ORM avec gestion du **Soft Delete (`deleted_at`)** et d'alimentation automatique de la base de données par scripts de **Seeding**.

---

## 🏗️ Structure Actuelle du Module `api`

Les modèles de données et les commandes d'administration ont été structurés dans le module `api/` :

```text
backend/
├── api/
│   ├── apps.py                  # Configuration de l'application API & enregistrement des signals
│   ├── fixtures/
│   │   └── iso_27001_controls.json # Jeu de données des 93 contrôles ISO 27001:2022
│   ├── management/
│   │   └── commands/
│   │       ├── seed_iso_controls.py # Seeder du référentiel ISO 27001
│   │       └── seed_demo_data.py    # Seeder dynamique multi-modèles (Faker)
│   ├── models/                  # Modèles de données ORM
│   │   ├── __init__.py          # Export centralisé des modèles
│   │   ├── base.py              # TimeStampedUUIDModel, SoftDeleteQuerySet, SoftDeleteManager
│   │   ├── organization.py      # Organization, Scope, UserOrganizationRole, UserScopeAccess
│   │   ├── iso27001.py          # Asset, Risk, IsoControl, SoaEntry, TreatmentTask, Evidence, SoaVersion
│   │   └── support.py           # UserPreference, SystemSetting
│   └── signals.py               # Instanciation automatique des SoaEntry à la création d'un Scope
├── core/                        # Configuration globale du projet Django
│   ├── settings.py              # Configuration INSTALLED_APPS, DATABASES, etc.
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
* **UserScopeAccess** : Accès granulaire d'un membre d'organisation à un périmètre (`Scope`) spécifique.

#### 3. Core ISO 27001 (`api/models/iso27001.py`)
* **Asset** : Patrimoine à protéger lié à un périmètre. Contient l'évaluation DIC (1 à 3) (`confidentiality`, `integrity`, `availability`).
* **Risk** : Scénarios d'incidents identifiés sur un actif (Vraisemblance 1-5, Impact 1-5, statut : `OPEN`, `IN_MITIGATION`, `ACCEPTED`, `CLOSED`).
* **IsoControl** : Catalogue global des 93 mesures ISO 27001:2022 réparties par thème (`ORGANIZATIONAL`, `PEOPLE`, `PHYSICAL`, `TECHNOLOGICAL`).
* **SoaEntry** : Déclaration d'applicabilité (SoA) liée à un périmètre et à une mesure (`NOT_IMPLEMENTED`, `IN_PROGRESS`, `IMPLEMENTED`).
* **TreatmentTask** : Plan de traitement des risques. La complétion d'une tâche met automatiquement à jour le statut du contrôle SoA correspondant via la surcharge de `save()`.
* **Evidence** : Stockage des fichiers de preuves liées aux tâches de traitement.
* **SoaVersion** : Instantané (snapshot JSON) figé d'une SoA pour audit (`DRAFT`, `APPROVED`).

#### 4. Support & Configuration (`api/models/support.py`)
* **UserPreference** : Langue, thème (`LIGHT`, `DARK`, `SYSTEM`), fuseau horaire, notifications email.
* **SystemSetting** : Clef/valeur dynamique (stockage au format `JSONField`).

---

## 🚀 Initialisation, Migrations & Seeding

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

### 🌱 Alimentation de la Base de Données (Seeders)
Le projet utilise une approche à deux niveaux pour le peuplement de la base de données : un seeder pour le référentiel normatif fixe et un seeder dynamique pour les données métier.

#### 1. Charger le Référentiel ISO 27001:2022
Cette commande importe les 93 mesures officielles de l'Annexe A (titres, thèmes et descriptions) depuis le fichier JSON `api/fixtures/iso_27001_controls.json`.
```bash
python manage.py seed_iso_controls
```
*Note : Cette commande est idempotente (`update_or_create`). Elle peut être exécutée plusieurs fois sans créer de doublons.*

#### 2. Générer les Données de Démonstration Multi-Modèles
Cette commande peuple dynamiquement l'intégralité de la BDD avec la bibliothèque `Faker` (Organisations, Utilisateurs, Rôles RBAC, Périmètres, Actifs, Risques, Tâches de traitement, Préférences) ainsi que le compte d'administration global `admin_global` (mot de passe : `Admin1234!`).

##### 🔹 Options et Paramètres disponibles :

| Option | Description | Valeur par défaut | Exemple d'utilisation |
| :--- | :--- | :--- | :--- |
| `--count` | Nombre d'organisations virtuelles à générer | `3` | `--count 5` |
| `--clear` | Purge l'ensemble des données métiers existantes avant d'exécuter le seeder | Désactivé | `--clear` |

##### 💡 Exemples d'utilisation :
* Générer des données par défaut (cumulatif) :
  ```bash
  python manage.py seed_demo_data
  ```
* Définir un nombre spécifique d'organisations à ajouter :
  ```bash
  python manage.py seed_demo_data --count 5
  ```
* Réinitialiser et recommencer à zéro (Reset complet des données métiers) :
  ```bash
  python manage.py seed_demo_data --clear --count 3
  ```

### 4. Lancer le serveur local
```bash
python manage.py runserver
```
