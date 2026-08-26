# Ingestion des données personnelles

GrepoIntel ne se connecte jamais à Grepolis, ne reçoit ni cookie, ni mot de passe, ni jeton de session.

| Option | Couverture | Sécurité | Risque de maintenance | Décision V2 |
|---|---|---|---|---|
| JSON/CSV manuel | élevée si export complet | excellente | faible | retenue |
| Copier/coller | partielle | excellente | faible | complément |
| Export officiel | à confirmer selon le jeu | excellente | faible | à étudier |
| Companion navigateur local | potentiellement élevée | moyenne | élevée / règles à valider | non implémenté |

Le seul chemin V2 est donc un import explicite initié par l’utilisateur. Le format `grepointel-personal-state` est versionné, validé avant écriture et stocké uniquement dans PostgreSQL local.
