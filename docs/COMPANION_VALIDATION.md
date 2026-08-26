# Validation du companion Grepolis

## Internals identifiés par l’adapter

L’adapter isole les candidats de runtime dans `companion/src/adapters/grepolis/adapter.ts` : `ITowns.towns`, `Game.towns`, `GameData`, `Game.player` et `heroes`. Il ne lit ni le DOM ni les cookies et n’effectue ni `fetch`, ni clic, ni commande Grepolis.

| Catégorie | Couverture d’architecture | Validation live |
|---|---|---|
| Joueur / monde | adapter + bridge | requise |
| Liste des villes | adapter + normalisation | requise |
| Ressources, population, bâtiments, recherches, unités | adapter tolérant aux variantes | requise |
| Dieu, héros, files | format canonique + diagnostic partiel | requise |
| Mouvements | non extrait tant qu’une collection passive fiable n’est pas identifiée | non validée |

## Validation live

**LIVE GREPOLIS EXTRACTION: REQUIRES USER BROWSER VALIDATION.** L’environnement de développement ne fournit pas une session Grepolis connectée. Le flux extension → API protégée → PostgreSQL est néanmoins implémenté ; il faut charger l’extension, l’appairer, puis utiliser le diagnostic retourné par la première synchronisation pour ajuster l’adapter si le client a changé.
