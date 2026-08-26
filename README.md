# GrepoIntel

GrepoIntel est un tableau de renseignement stratégique local pour Grepolis. Il est volontairement **externe et en lecture seule** : il importe des exports publics, accepte un profil local et produit des analyses. Il ne se connecte pas au client Grepolis, n’injecte aucun script et n’envoie aucun ordre.

## Démarrage

```powershell
Copy-Item .env.example .env
docker compose up --build
docker compose exec backend python -m app.seed
```

- Frontend : `http://localhost:13100`
- API : `http://localhost:18000`
- Swagger : `http://localhost:18000/docs`
- PostgreSQL : `localhost:15433`
- Redis : `localhost:16379`

Le backend applique les migrations au démarrage. Le seed est idempotent et fournit le monde FR183, un profil, cinq villes personnelles, vingt voisins, quatre alliances, snapshots et événement de conquête.

## Utilisation

1. Ouvrir l’accueil puis associer le pseudo Grepolis exact.
2. Utiliser **Importer FR183** pour actualiser les exports publics joueurs, alliances, villes et classements de combat.
3. Naviguer vers Dashboard, Carte, Joueurs, Alliances, Cibles, Menaces, Événements et Planificateur.

L’import sauvegarde des snapshots, dérive les changements de propriétaire et d’alliance, et ne duplique pas les identifiants externes. Une tâche APScheduler relance la collecte toutes les deux heures (configurable par `SNAPSHOT_INTERVAL_HOURS`). Un verrou Redis par monde empêche les imports simultanés (`409` lorsqu’une collecte est déjà active).

## Architecture

```text
collectors → import_service → PostgreSQL snapshots/events → analytics → FastAPI → Next.js
```

- `backend/app/collectors/providers/grepolis_public.py` : fournisseur HTTP public avec délais et erreurs contrôlés.
- `backend/app/services/import_service.py` : normalisation, stockage, snapshots et événements dérivés.
- `backend/app/analytics/` : distance unique, scores explicables, cluster et règles FR183.
- `backend/app/jobs/snapshots.py` : collecte périodique.
- `frontend/` : Next 16, React 19, TypeScript, Tailwind, composants Watermelon UI/shadcn, TanStack Query et MapLibre.

## API

Les collections `players`, `cities` et `alliances` sont paginées avec `world_id`, `limit` et `offset`. Les routes principales sont :

```text
GET  /api/worlds                 GET /api/me
GET  /api/players/{id}           GET /api/cities/{id}
GET  /api/alliances/{id}         GET /api/dashboard
GET  /api/analytics/cluster      GET /api/analytics/threats
GET  /api/analytics/targets      GET /api/events
POST /api/planner/travel         POST /api/planner/revolt
POST /api/worlds/{id}/import     PUT /api/me
```

`/api/planner/*` est purement informatif. Les requêtes utilisent des modèles Pydantic et le planificateur ne contient volontairement aucun mécanisme d’envoi vers le jeu.

## Vérification et tests

```powershell
docker compose exec backend pytest
docker compose exec backend python -m app.seed
Invoke-WebRequest http://localhost:18000/health
```

Les tests couvrent distance, temps de trajet, scores, cohésion de cluster, fenêtre de révolte, endpoints principaux, pagination, erreurs 404/422, santé PostgreSQL/Redis et idempotence du seed. Les règles FR183 sont centralisées dans `backend/app/analytics/world_rules/fr183.py`; elles ne sont pas recopiées dans React.

## Configuration et sécurité

Copier uniquement `.env.example`; ne jamais versionner `.env`. CORS est configurable avec `CORS_ORIGINS`. Les données publiques externes sont récupérées avec un User-Agent, timeout, retry/backoff et une fréquence modérée. Les estimations d’activité ne prétendent jamais connaître une connexion réelle d’un joueur.

Voir [ROADMAP.md](ROADMAP.md) pour les limites connues et la suite planifiée.
