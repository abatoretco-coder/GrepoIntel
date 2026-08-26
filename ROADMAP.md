# Roadmap GrepoIntel

## NOW

- Import public FR183, carte, menaces/cibles et contexte Abator fonctionnels.
- Companion Firefox en lecture seule : villes, ressources, armées, bâtiments, recherches, dieu et fraîcheur synchronisés. Héros assignés et files restent partiels.
- Catalogue Grepolis unique exposé par `/api/game-data/units` : unités terrestres, navales et mythiques, rôles, statistiques de base, population, vitesse, transport, dieu et prérequis.
- Moteur combat V1 : attaque et trois défenses terrestres, naval séparé, mur observé, et incertitudes explicites pour moral, chance, nuit, recherches, héros, dieu et paramètres FR183.
- Simulateur connecté : ville d’origine et armée issues du dernier snapshot Firefox, renseignement cible choisi par nom, composition structurée, ratios sol/naval et confiance visible. Il n’envoie aucun ordre.
- Avis de combat en lecture seule : re-reconnaissance, naval clear, land clear, re-clean et révolte lorsque le renseignement et les armées le permettent.

## NEXT

- Parser passivement les rapports/observations disponibles dans Firefox avec provenance et âge.
- Compléter l’extracteur de héros possédés/affectés et des files ; ne pas confondre catalogue et possessions.
- Défense advisor : composition DEF, attaques reçues, risque de conquête et alerte de re-reconnaissance.
- Recommandations micro liées aux menaces, îles et alliances de la macro.

## LATER

- Opérations multi-villes : consolider les étapes naval clear, land clear, re-clean et conquête/révolte, sans automatisation de jeu.
- Optimisation globale héros/dieux et calibration du moteur à partir de combats observés.
- Paramètres FR183 vérifiés par monde (moral, nuit, vitesse, événements) et jeux de fixtures réels anonymisés.
- Tests navigateur Firefox de bout en bout, tests de précision du moteur de combat et tests de responsive visuel.
