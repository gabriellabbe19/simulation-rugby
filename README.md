# Tour de France — Historique des étapes et des villes

Données dérivées de l'historique des étapes du Tour de France (éditions 1947–2026).

## Fichiers

- `data/TDF_Stages_History.csv` — étapes brutes (année, étape, départ, arrivée), encodage Windows-1252, séparateur `;`
- `data/TDF_Villes_History.csv` — agrégation par ville, UTF-8 (BOM), séparateur `;`, prêt à géocoder (uMap) :

| Colonne | Description |
|---|---|
| `ville` | nom de la ville (variantes normalisées) |
| `pays` | pays (France, Belgique, Suisse, …) |
| `nb_departs` / `nb_arrivees` / `nb_total` | compteurs de passages |
| `premiere_edition` / `derniere_edition` | années extrêmes |
| `editions` | liste des éditions concernées |
| `description` | détail des étapes (ex. « départ étape 11 du Tour 1987 ») |
