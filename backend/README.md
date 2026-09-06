# 🛡️ OpenSMR — Backend API

Backend Django REST Framework pour la gestion du Système de Management de la Sécurité de l'Information (SMSI) conforme à la norme **ISO/IEC 27001:2022**.

Le projet repose sur une architecture **Selector / Service**, une gestion fine des droits **RBAC Multi-tenant** (Organisation & Scope) via JWT, et un suivi automatisé de la conformité normative.

---

## 🏗️ Structure du Projet

L'application est structurée de manière modulaire au sein du dossier `api/` :

```text
backend/
├── api/
│   ├── apps.py                  # Configuration de l'API & enregistrement des signals
│   ├── fixtures/
│   │   └── iso_27001_controls.json # Référentiel des 93 contrôles ISO 27001:2022
│   ├── management/
│   │   └── commands/
│   │       ├── seed_iso_controls.py # Seeder du référentiel ISO
│   │       └── seed_demo_data.py    # Seeder dynamique d'environnement de dev (Faker)
│   ├── models/                  # Modèles de données ORM avec Soft Delete
│   │   ├── base.py              # TimeStampedUUIDModel, SoftDeleteManager
│   │   ├── organization.py      # Organization, Scope, UserOrganizationRole, UserScopeAccess
│   │   ├── iso27001.py          # Asset, Risk, IsoControl, SoaEntry, TreatmentTask, Evidence, SoaVersion
│   │   └── support.py           # UserPreference, SystemSetting
│   ├── modules/
│   │   └── v1/                  # API v1 (pattern Selector / Service)
│   │       ├── auth/            # Authentification, Inscription & JWT Context Switch
│   │       │   ├── selectors.py
│   │       │   ├── services.py
│   │       │   ├── serializers.py
│   │       │   ├── views.py
│   │       │   └── urls.py
│   │       └── permissions.py   # Rôles RBAC (ADMIN, RSSI, RISK_OWNER, AUDITOR)
│   └── signals.py               # Génération automatique du SoA à la création d'un Scope
├── core/                        # Configuration globale Django (settings, urls)
└── manage.py
```

---

## 🔑 Authentification & Architecture Multi-tenant (JWT)

L'authentification est basée sur SimpleJWT avec injection dynamique du contexte d'exécution dans les tokens.

### Features Authentification & RBAC :
* **Payload JWT enrichi** : Le token d'accès contient `organization_id`, `role` et `scope_id` actifs.
* **Context Switching (`/switch-context/`)** : Permet à un utilisateur appartenant à plusieurs organisations ou périmètres (Scopes) de basculer de contexte en régénérant ses tokens sans se re-connecter.
* **Tolérance aux comptes sans périmètre** : Un utilisateur sans organisation ou sans scope attribué peut se connecter (claims positionnés à `null`) et accéder à son profil.
* **Rôles RBAC gérés** : `ADMIN`, `RSSI`, `RISK_OWNER`, `AUDITOR`.

---

## 📚 Documentation OpenAPI & Swagger UI

L'API est documentée de manière interactive avec `drf-spectacular`.

Une fois le serveur démarré, accédez à la documentation via :
* **Swagger UI** : `http://127.0.0.1:8000/api/docs/`
* **ReDoc** : `http://127.0.0.1:8000/api/redoc/`
* **Schéma OpenAPI (JSON)** : `http://127.0.0.1:8000/api/schema/`

*Note : L'interface Swagger prend en charge l'authentification Bearer `<votre_token_jwt>`.*

---

## ⚡ Prise en Main Rapide

### 1. Cloner & Activer l'Environnement Virtuel
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Installer les Dépendances
```bash
pip install -r requirements.txt
```

### 3. Exécuter les Migrations Base de Données
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Alimenter la Base de Données (Seeding)

#### A. Charger le référentiel normatif ISO 27001:2022 (93 mesures)
```bash
python manage.py seed_iso_controls
```

#### B. Générer des données de démonstration (Organisations, Utilisateurs, Risques...)
```bash
# Génération standard (3 organisations)
python manage.py seed_demo_data

# Réinitialiser complètement la base métier et générer 5 organisations
python manage.py seed_demo_data --clear --count 5
```

**Compte Administrateur Global généré par le seeder :**
* **Username** : `admin_global`
* **Password** : `Admin1234!`

### 5. Lancer le Serveur de Développement
```bash
python manage.py runserver
```

---

## 🔌 Endpoints de l'API (`/api/v1/auth/`)

| Méthode | Endpoint | Description | Accès |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/auth/register/` | Inscription utilisateur (crée l'utilisateur + optionnellement son organisation) | Public |
| **POST** | `/api/v1/auth/login/` | Connexion et émission des tokens JWT (`access` & `refresh`) | Public |
| **POST** | `/api/v1/auth/refresh/` | Rafraîchissement du token d'accès JWT | Public |
| **POST** | `/api/v1/auth/switch-context/` | Régénération des tokens pour cibler un autre `organization_id` ou `scope_id` | Authentifié |
| **GET** | `/api/v1/auth/me/` | Profil de l'utilisateur connecté et liste de ses rôles | Authentifié |
