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

Le frontend fonctionne actuellement sans le backend grâce à un mock d'authentification activé dans `src/app/core/config/api.config.ts`.

Compte disponible :

```text
Identifiant : demo@opensmr.fr
Mot de passe : Demo1234!
```

Le mode mock permet de tester :

- la connexion et l'inscription ;
- le chargement du profil ;
- les JWT ;
- le changement d'organisation et de périmètre ;
- la protection des routes ;
- les autorisations par rôle.

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
│       │   └── auth/               connexion et inscription
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

Chaque domaine fonctionnel possède son propre dossier. Les futurs modules `assets`, `risks`, `treatments`, `soa` et `my-tasks` doivent rester isolés dans ce dossier.

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
| `/dashboard` | Authentifié | Accueil temporaire et contexte actif |
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
- utiliser des messages de commit en français ;
- limiter chaque commit à deux fichiers ;
- lancer les tests et le build avant de partager les modifications.

## État actuel

Fonctionnalités terminées :

- configuration de `HttpClient` ;
- interceptor JWT et rafraîchissement de session ;
- état d'authentification avec Signals ;
- changement de contexte multi-tenant ;
- connexion et inscription ;
- topbar globale ;
- guards d'authentification et de rôles ;
- backend d'authentification mocké.

Prochain module prévu : inventaire des actifs dans `/assets`.
