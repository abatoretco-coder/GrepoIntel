# GrepoIntel Companion

Extension WebExtension locale, passive et **en lecture seule**. Elle n’ouvre aucune ville, ne clique jamais dans Grepolis et n’envoie aucune requête au jeu. Son seul flux est : runtime déjà chargé → snapshot nettoyé → `localhost` GrepoIntel.

## Installation de développement

1. Ouvrir ce dossier dans un terminal et lancer `npm install`, puis `npm run build`.
2. Dans Chromium : `chrome://extensions` → activer le mode développeur → **Charger l’extension non empaquetée** → sélectionner `companion/`.
3. Dans Firefox : `about:debugging#/runtime/this-firefox` → **Charger un module complémentaire temporaire** → sélectionner `companion/manifest.json`.
4. Dans GrepoIntel, générer un jeton d’appairage via `POST /api/personal-state/pairing`, puis le copier dans le popup. Ce jeton est propre à GrepoIntel : ce n’est ni un cookie ni une donnée Grepolis.
5. Ouvrir une page Grepolis connectée et cliquer **Sync now**.

## Modes

- `MANUAL` (défaut) : uniquement le bouton du popup.
- `ON_PAGE_LOAD` : une capture passive au chargement de la page.
- `PERIODIC` : toutes les cinq minutes ou plus, sur les onglets Grepolis déjà ouverts.

## Adapter et diagnostic

`src/adapters/grepolis/adapter.ts` est la seule couche qui sonde les collections du client. Il effectue uniquement des lectures et retourne un diagnostic par catégorie. Une collection indisponible devient `PARTIAL` ou `FAILED`; elle ne bloque pas les autres données.

Les candidats actuellement testés de manière *duck-typed* sont `ITowns.towns`, `Game.towns`, `GameData`, `Game.player` et les collections globales `heroes`. Ils sont des hypothèses d’adaptation, non une validation live : la structure exacte doit être confirmée dans le navigateur connecté de l’utilisateur.

## Sécurité

Le sanitiseur récursif retire toute clé contenant notamment `cookie`, `password`, `csrf`, `token`, `session`, `authorization` ou `auth` avant sérialisation. Le token d’appairage est seulement un en-tête HTTP ; il n’entre jamais dans le snapshot. L’extension ne possède aucune permission d’écriture dans Grepolis.
