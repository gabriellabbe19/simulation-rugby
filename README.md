# Simulation Rugby 🏉

Simulateur de match de rugby à XV écrit en Python (sans dépendance externe).

## Lancer une simulation

```bash
python3 simulateur.py
```

Le programme demande le nom des deux équipes, génère leurs caractéristiques
(attaque, défense, physique, discipline) puis simule un match de 80 minutes
avec commentaires en direct : essais, transformations, pénalités, drops,
fautes, pertes de balle...

## Personnaliser les équipes

Les statistiques sont générées aléatoirement (60-90) à chaque match.
Pour des équipes fixes, importez la classe `Equipe` :

```python
from simulateur import Equipe, Match

france = Equipe("France", attaque=88, defense=82, physique=80, discipline=75)
nz = Equipe("Nouvelle-Zélande", attaque=92, defense=85, physique=90, discipline=70)
Match(france, nz).simuler()
```

## Structure des points

- Essai : 5 points
- Transformation : 2 points
- Pénalité : 3 points
- Drop : 3 points
