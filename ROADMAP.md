# Roadmap GrepoIntel

## ✅ Fonctionnel et testé

- Docker Compose, PostgreSQL 16, Redis, FastAPI et Next.js démarrent sur volume vide.
- Migration Alembic et seed idempotent (`python -m app.seed`).
- Import public officiel FR183 : joueurs, alliances, villes et classements de combat ; noms URL-décodés, timeout/retry bornés et métriques de collecte.
- Snapshots et événements dérivés, verrou Redis par monde et scheduler APScheduler à deux heures.
- API de lecture, planificateur informatif avec convention `Europe/Paris`, healthcheck PostgreSQL/Redis.
- Dashboard, carte MapLibre et écrans frontend reliés à l’API.
- Tests analytiques et intégration API/database ; lint et build frontend.

## ⚠️ Implémenté mais à améliorer

- Le routeur API reste regroupé dans `backend/app/api/router.py`; une séparation par domaine est souhaitable avant une expansion fonctionnelle importante.
- Les analyses menaces/cibles et le dashboard restent adaptés aux volumes V1, mais nécessiteront des requêtes groupées supplémentaires et du cache Redis pour des dizaines de milliers de joueurs.
- La carte affiche les coordonnées publiques Grepolis ; clustering et filtres interactifs avancés ne sont pas encore disponibles.

## ❌ Non implémenté

- Notifications, Discord, multi-mondes, données privées d’armée, analyse de mouvements, PostGIS et recommandations avancées.
