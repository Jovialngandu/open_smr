# OpenSMR - Frontend Angular

Interface web du système de management des risques de sécurité de l'information OpenSMR, basé sur ISO 27001:2022.

## Prérequis

- Node.js 22 ou une version compatible avec Angular 21 ;
- npm 11 recommandé ;
- Git ;
- le backend Django, uniquement lorsque les mocks sont désactivés.

Vérifier l'environnement :

```bash
node --version
npm --version
```

## Installation

Depuis la racine du dépôt :

```bash
cd frontend
npm install
```

Lancer le serveur de développement :

```bash
npm start
```

Ouvrir ensuite :

```text
http://localhost:4200
```

Le serveur recharge automatiquement l'application après une modification du code.

## Mode de démonstration

Le frontend fonctionne actuellement sans le backend grâce aux mocks couvrant l'ensemble du parcours MVP, activés dans `src/app/core/config/api.config.ts`.

Compte disponible :

```text
Identifiant : demo@opensmr.fr
Mot de passe : Demo1234!
```

Le compte `owner@opensmr.fr` avec le même mot de passe permet de tester directement le rôle `RISK_OWNER` et la page `/my-tasks`. Le compte principal peut basculer vers l'organisation Novacare pour tester le rôle `AUDITOR` et le portail d'audit.

Le mode mock permet de tester :

- la connexion et l'inscription ;
- le chargement du profil ;
- les JWT ;
- le changement d'organisation et de périmètre ;
- la protection des routes ;
- les autorisations par rôle.
- l'inventaire des actifs, son filtrage par périmètre et son CRUD ;
- le registre des risques, son filtrage par périmètre et son CRUD.
- le dashboard, ses indicateurs et la heatmap interactive 5 × 5 ;
- les plans de traitement et leur suivi ;
- le tableau Kanban des traitements avec glisser-déposer entre les statuts ;
- le dépôt de preuves et la clôture des tâches ;
- les 93 mesures de la SoA, leur édition et leur synchronisation simulée ;
- les exports PDF/CSV simulés ;
- le portail auditeur en lecture seule ;
- les comptes, rôles et statuts des utilisateurs.

## Connexion au backend Django

L'API attendue par défaut est :

```text
http://127.0.0.1:8000/api/v1
```

Pour utiliser Django, modifier `src/app/core/config/api.config.ts` :

```typescript
export const API_CONFIG = {
  baseUrl: 'http://127.0.0.1:8000/api/v1',
  useMocks: false,
  mockDelayMs: 550,
} as const;
```

Le backend doit autoriser l'origine `http://localhost:4200` dans sa configuration CORS.

Endpoints utilisés :

```text
POST /api/v1/auth/login/
POST /api/v1/auth/register/
POST /api/v1/auth/refresh/
GET  /api/v1/auth/me/
POST /api/v1/auth/switch-context/
GET|POST /api/v1/assets/
PUT|DELETE /api/v1/assets/{id}/
GET|POST /api/v1/risks/
PUT|DELETE /api/v1/risks/{id}/
GET /api/v1/heatmap/?scope_id={scope_id}
GET|POST /api/v1/treatments/
PATCH /api/v1/treatments/{id}/
PATCH /api/v1/treatments/{id}/complete/
POST /api/v1/treatment/evidences/
GET /api/v1/soa/?scope_id={scope_id}
PATCH /api/v1/soa/{id}/
GET /api/v1/scopes/{scope_id}/soa/export/?format=pdf|csv
GET|POST /api/v1/users/
PATCH /api/v1/users/{id}/
```

Attention : le formulaire accepte un email ou un identifiant, mais le contrat Django actuel utilise la propriété `username` pour la connexion.

## Organisation du projet

```text
frontend/
├── public/                         fichiers statiques
├── src/
│   ├── index.html                  document HTML principal
│   ├── main.ts                     point d'entrée Angular
│   ├── styles.scss                 styles globaux et responsive
│   └── app/
│       ├── app.config.ts           fournisseurs globaux
│       ├── app.routes.ts           routes et permissions
│       ├── core/                   logique transversale singleton
│       │   ├── config/             configuration de l'API
│       │   ├── guards/             protection des routes
│       │   ├── interceptors/       JWT et mocks HTTP
│       │   ├── models/             contrats TypeScript
│       │   └── services/           état et logique globale
│       ├── features/               fonctionnalités métier
│       │   ├── auth/               connexion et inscription
│       │   ├── assets/             inventaire des actifs
│       │   ├── risks/              registre des risques
│       │   ├── dashboard/          matrice des risques
│       │   ├── treatments/         plans de traitement
│       │   ├── my-tasks/           tâches et preuves
│       │   ├── soa/                déclaration d'applicabilité
│       │   ├── audit/              portail auditeur
│       │   └── users/              comptes et habilitations
│       └── shared/                 composants réutilisables
│           ├── components/          topbar et composants communs
│           └── pages/               pages transversales
├── angular.json                   configuration Angular CLI
├── package.json                   commandes et dépendances
└── tsconfig.json                  configuration TypeScript stricte
```

## Principes d'architecture

### `core`

Contient les éléments instanciés globalement : authentification, stockage des tokens, contexte actif, guards, interceptors et modèles communs.

### `features`

Chaque domaine fonctionnel possède son propre dossier : `assets`, `risks`, `dashboard`, `treatments`, `soa`, `my-tasks`, `audit` et `users`.

### `shared`

Contient uniquement les composants réutilisables par plusieurs fonctionnalités, par exemple la topbar ou une page d'erreur.

### Composants Angular

Les composants sont standalone. Le TypeScript et le HTML sont toujours séparés :

```text
nom.component.ts
nom.component.html
```

Le fichier TypeScript gère l'état et les actions. Le fichier HTML gère la structure visible et les liaisons Angular.

## Routes disponibles

| Route | Accès | Description |
|---|---|---|
| `/login` | Public | Connexion |
| `/register` | Public | Inscription |
| `/dashboard` | Authentifié | Indicateurs, heatmap et priorités |
| `/assets` | ADMIN, RSSI, RISK_OWNER | Inventaire des actifs |
| `/risks` | ADMIN, RSSI, AUDITOR | Registre des risques |
| `/treatments` | ADMIN, RSSI, RISK_OWNER | Plans de traitement |
| `/soa` | Tous les rôles | Déclaration d'applicabilité |
| `/users` | ADMIN, RSSI | Utilisateurs et habilitations |
| `/my-tasks` | RISK_OWNER | Tâches assignées |
| `/audit-view` | AUDITOR | Portail d'audit en lecture seule |
| `/access-denied` | Authentifié | Erreur d'autorisation 403 |

Les pages sont chargées à la demande avec `loadComponent` afin de limiter le JavaScript initial.

## Commandes utiles

```bash
# Serveur local
npm start
ng serve

# Build de production
npm run build

# Tests unitaires sans mode interactif
npm test -- --watch=false

# Vérification TypeScript
npx tsc -p tsconfig.app.json --noEmit
```

Le build compilé est généré dans `dist/frontend/` et ne doit pas être ajouté à Git.

## Ajouter une fonctionnalité

Pour créer un nouveau module métier :

1. créer son dossier dans `src/app/features/` ;
2. créer les modèles TypeScript correspondant au contrat de l'API ;
3. créer un service pour les appels HTTP et l'état du module ;
4. créer un composant `.ts` et son template `.html` ;
5. ajouter des données mockées si l'API n'est pas disponible ;
6. enregistrer la route dans `app.routes.ts` ;
7. ajouter `authGuard` et les rôles autorisés ;
8. ajouter les tests unitaires ;
9. exécuter les tests et le build.

Exemple de route privée :

```typescript
{
  path: 'assets',
  canActivate: [authGuard, roleGuard],
  data: { roles: ['ADMIN', 'RSSI', 'RISK_OWNER'] },
  loadComponent: () =>
    import('./features/assets/pages/asset-list.component')
      .then((module) => module.AssetListComponent),
}
```

## Conventions de contribution

- utiliser des noms de fichiers en `kebab-case` ;
- conserver le HTML et le TypeScript dans des fichiers séparés ;
- utiliser les Signals pour les états réactifs globaux ;
- typer les requêtes et les réponses HTTP ;
- afficher des messages compréhensibles par l'utilisateur ;
- préserver la navigation au clavier et les attributs ARIA ;
- ne jamais ajouter de secret ou de vrai token au dépôt ;
- lancer les tests et le build avant de partager les modifications.

## Suivi des traitements

La page `/treatments` propose deux présentations :

- une vue Tableau de type Kanban, organisée en colonnes « À faire », « En cours » et « Terminées » ;
- une vue Liste adaptée à la lecture détaillée et aux petits écrans.

Une carte peut être déplacée à la souris entre les colonnes. Le sélecteur présent sur chaque carte offre la même action au clavier et sur mobile. La mise à jour est optimiste : la carte se déplace immédiatement, puis revient à sa position précédente si l'API refuse la modification. Une tâche ne peut pas être terminée tant qu'aucune preuve n'est jointe.

Les filtres permettent de rechercher par action, risque, mesure ISO ou responsable. Chaque carte présente le responsable, l'échéance, le risque, la mesure et le nombre de preuves sans devoir ouvrir une autre page.

## Comportement des formulaires

Les formulaires Actif, Risque, Traitement, Preuve et Utilisateur :

- valident les champs requis avant l'appel HTTP ;
- refusent les valeurs constituées uniquement d'espaces ;
- attendent le chargement des listes dépendantes avant d'autoriser la soumission ;
- affichent une erreur près du champ concerné ;
- désactivent l'action principale pendant l'enregistrement ;
- affichent une confirmation et rendent le nouvel élément visible après la réussite.

Le formulaire Risque sélectionne automatiquement le premier actif une fois le chargement terminé, tout en conservant un choix effectué manuellement.

## État actuel

Fonctionnalités terminées :

- configuration de `HttpClient` ;
- interceptor JWT et rafraîchissement de session ;
- état d'authentification avec Signals ;
- changement de contexte multi-tenant ;
- connexion et inscription ;
- topbar globale ;
- guards d'authentification et de rôles ;
- backend d'authentification mocké ;
- inventaire des actifs avec badge DIC et formulaire de création/édition ;
- registre des risques avec score coloré et rattachement aux actifs ;
- mocks CRUD des actifs et des risques, filtrés par le périmètre actif.
- dashboard avec indicateurs, tâches urgentes et heatmap filtrante ;
- plans de traitement avec mesure ISO, responsable et échéance ;
- espace Mes tâches avec dépôt de preuves PDF/image et clôture ;
- SoA de 93 mesures avec édition en ligne et exports ;
- portail auditeur en lecture seule avec téléchargement des preuves ;
- gestion des utilisateurs et révocation des accès ;
- mocks HTTP pour tous les modules du MVP.

## Travail restant : connexion au backend réel

Le frontend du MVP est fonctionnel en mode mock. Pour le raccorder à Django :

1. vérifier chaque URL et chaque nom de champ avec les serializers DRF ;
2. implémenter côté backend les endpoints encore absents, notamment les exports, les preuves et la heatmap ;
3. garantir l'isolation par `organization_id` et `scope_id` côté serveur ;
4. implémenter côté Django les snapshots `SoaVersion` et la notification quotidienne des tâches en retard ;
5. remplacer `useMocks: true` par `useMocks: false` ;
6. exécuter les tests d'intégration avec le backend et vérifier les téléchargements réels.

Les guards et filtres frontend améliorent l'expérience utilisateur, mais les permissions RBAC doivent toujours être appliquées par Django.
