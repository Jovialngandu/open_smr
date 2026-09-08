# OpenSMR Frontend

Interface Angular du système de management des risques ISO 27001:2022 OpenSMR.

## Démarrage

```bash
npm install
npm start
```

L'application est disponible sur `http://localhost:4200`.

Les services d'authentification utilisent actuellement un backend mocké. Le compte de démonstration est :

- identifiant : `demo@opensmr.fr`
- mot de passe : `Demo1234!`

Pour brancher l'API Django, passer `useMocks` à `false` dans `src/app/core/config/api.config.ts`. L'URL attendue est `http://127.0.0.1:8000/api/v1`.

## Qualité

```bash
npm run build
npm test -- --watch=false
```

Le projet utilise des composants standalone, les formulaires réactifs, les Signals Angular et une compilation TypeScript stricte.
