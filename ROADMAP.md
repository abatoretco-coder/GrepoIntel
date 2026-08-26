# Roadmap GrepoIntel

## Livré

- Stack locale Docker : Next.js 16/React 19, FastAPI, PostgreSQL 16 et Redis.
- Modèle de données complet : monde, joueurs, villes, alliances, snapshots, conquêtes, changements d’alliance et profil local.
- Import public FR183 normalisé, historique à chaque collecte et détection d’événements entre deux états.
- Planification APScheduler toutes les deux heures, sans automatisation du jeu.
- API paginée et typée ; dashboard, profils détaillés, tableau d’événements et planificateur validé par Pydantic.
- Interface command center sombre avec composants Watermelon UI/shadcn, cache TanStack Query, carte MapLibre et navigation complète.
- Scoring explicable de menace/cible, estimation d’activité, cluster et règles de révolte FR183.

## À compléter avec davantage de données historiques

1. Graphiques Recharts plus riches dès que le serveur aura accumulé plusieurs jours de snapshots.
2. Filtres géographiques avancés et regroupement des marqueurs MapLibre pour les mondes volumineux.
3. Alertes de pression de frontière et comparaison Alliance vs Alliance à partir de séries de conquêtes plus longues.
4. Cache Redis de résultats analytiques et verrou distribué de collecte si plusieurs instances backend sont exécutées.

## Évolutions volontaires, hors V1

- Saisie manuelle ou import CSV de données privées (armées, ordres en cours), séparée des données publiques et toujours sans connexion au jeu.
- Multi-mondes, multi-profils et adaptateurs de fournisseurs publics alternatifs.
- Notifications opt-in (email, Discord, push).
- PostGIS si les requêtes de proximité dépassent les index `(world_id, x, y)` actuels.

## Principes non négociables

- Aucune interaction automatisée avec Grepolis.
- Toute estimation est expliquée par des signaux mesurables.
- Les règles du monde restent côté backend et sont configurables.
