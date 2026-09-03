# OpenSMR — Système de Management du Risque (ISO 27001)

> **Projet Académique :** GROUPE 24 • GOUVERNANCE DE SÉCURITÉ  
> **Sujet :** Développement d’une plateforme web de gestion des risques de sécurité de l’information selon la norme ISO 27001:2022.

---

## 👥 Membres du Groupe

| Nom & Prénom |
| :--- |
| **NGANDU KASEBA Jovial** <!-- Architecture Backend & Sécurité --> |
| **N'SANDUNU MUKALA Esther** <!-- Développement & Conformité ISO --> |
| **KASHAMA KADIADIA Exaucé** <!-- Interface Utilisateur (Frontend) --> |
| **MONGA MBAKA Ephraim** <!-- Documentation & Processus d'Audit --> |

---

## 🎯 Vision d'Ensemble & Objectifs Métier

Aujourd'hui, de nombreuses organisations gèrent leurs analyses de risques de sécurité sur des tableurs statiques et complexes à maintenir. **OpenSMR** vise à automatiser le cycle de gestion des risques ISO 27001 à travers une plateforme web moderne et dynamique articulée autour de 4 piliers :

1. **Inventaire des Actifs (Assets Management) :** Recensement des serveurs, bases de données et applications avec évaluation de leur criticité selon le critère **DIC** (Disponibilité, Intégrité, Confidentialité).
2. **Registre des Risques :** Évaluation des menaces (Calcul Vraisemblance × Impact) et visualisation dynamique via une **Heatmap 5x5**.
3. **Plan de Traitement des Risques :** Assignation de tâches correctives aux responsables techniques pour réduire les risques inacceptables.
4. **Déclaration d'Applicabilité (SoA) & Export :** Suivi automatisé des 93 contrôles de l'Annexe A (ISO 27001:2022) et génération du rapport d'audit.

### 💡 Innovations & "Touche Spéciale"

* **Lien Dynamique Tâches ➔ SoA :** Lorsqu'un responsable technique termine une tâche de sécurité et fournit sa preuve d'exécution, le contrôle ISO 27001 correspondant passe automatiquement à l'état `"Implémenté"` dans le tableau SoA en temps réel.
* **Portail Auditeur Externe :** Un accès sécurisé en lecture seule permettant à un auditeur de consulter la Déclaration d'Applicabilité, de contrôler les preuves déposées et de valider la conformité.

---

## 🏗️ Architecture Globale & Technologies

Le projet repose sur une architecture découplée orientée services :

* **Backend :** Django REST Framework (DRF) — Architecture modulaire versionnée (Pattern *Services / Selectors*).
* **Frontend :** React + Vite, Redux Toolkit, TailwindCSS & Material UI (MUI).
* **Base de données :** PostgreSQL (Production / Docker) ou SQLite (Développement local léger).

### Base de l'Arborescence du Dépôt

```text
open_smr/
├── README.md               # Documentation générale (Présent fichier)
├── docker-compose.yml      # Orchestration des conteneurs
├── .env.example            # Exemple de configuration des variables d'environnement
├── backend/                # Application Backend Django REST (voir backend/README.md)
└── frontend/               # Application Frontend React (voir frontend/README.md)
```

> 📌 Pour le détail complet des dossiers et composants internes, consultez les fichiers README.md dédiés dans `backend/` et `frontend/`.

---

## 🛠️ Modes de Développement & Configuration

### 1. Préparation du Fichier d'Environnement (.env)

Avant toute exécution, copiez le fichier d'exemple à la racine du projet :

```bash
cp .env.example .env
```

### Option A : Développement Rapide avec Docker Compose (Recommandé)

Lance la pile complète (PostgreSQL, Backend Django, Frontend React) dans des conteneurs isolés avec Hot-Reload activé.

```bash
# Lancer et construire l'ensemble des services
docker-compose up --build
```

* **Frontend :** `http://localhost:5173`
* **Backend API :** `http://localhost:8000/api/v1/`
* **Base de données PostgreSQL :** Accessible sur le port `5433` de la machine hôte pour éviter tout conflit avec un Postgres local (port interne `5422` conservé par le réseau Docker).

### Option B : Développement Direct en Local (Sans Docker)

Si vous développez directement sur votre machine sans utiliser Docker :

#### 1. Configuration & Lancement du Backend (Django REST)

```bash
cd backend

# Créer et activer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Sous Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer la base de données :
# Pour utiliser SQLite à la place de PostgreSQL, vérifiez la ligne suivante dans votre fichier .env :
# USE_SQLITE=True

# Appliquer les migrations
python manage.py migrate

# Lancer le serveur de dev Backend
python manage.py runserver
```

#### 2. Lancement du Frontend (React / Vite)

Dans un second terminal :

```bash
cd frontend

# Installer les paquets
npm install

# Démarrer le serveur de dev Vite
npm run dev
```

---

## 🔐 Protocoles & Sécurité

* **Authentification & Autorisation :** Gestion par jetons JWT / Sessions sécurisées et contrôle d'accès basé sur les rôles (RBAC : Administrateur, Responsable Risque, Agent Technique, Auditeur).
* **Transport :** Communications chiffrées via le protocole HTTPS / TLS.
* **Traçabilité & Audit :** Journalisation (Logging) des actions critiques pour garantir la non-répudiation des éléments de preuve apportés aux contrôles ISO.

---

## 🧪 Tests & Qualité

```bash
# Exécution des tests unitaires Backend
cd backend
python manage.py test

# Exécution du linter Frontend
cd frontend
npm run lint
```
