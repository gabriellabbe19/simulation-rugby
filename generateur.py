# -*- coding: utf-8 -*-
"""
Générateur de joueurs : système rating -> notes basé sur la taxonomie A-D.

Principe :
- Chaque poste classe ses 18 attributs en A (fondamentales), B (importantes),
  C (maîtrisées), D (bases) et 0 (non avenues).
- La note de chaque attribut = valeur de la table rating x catégorie + bruit
  uniforme [-5, +5], bornée [0, 99].
- Les attributs non avenues restent à 0.
- La moyenne générale M (entier) = PartieEntière[
      (0.5*MoyA + 0.25*MoyB + 0.15*MoyC + 0.10*MoyD) / SommeDesPoidsPrésents
      + 5 ]
  renormalisée par les poids présents (ex. n°8 sans D : division par 0.9).
"""

import random

ATTRIBUTS = [
    "Acceleration", "Power", "Skill", "Speed", "Stamina", "Strength",
    "Aggression", "Composure", "Creativity", "Leadership", "Positioning", "Tenacity",
    "Goal Kick", "Line Out", "Scrum", "Rucking", "Positional Kicking", "Tackling",
]

# Table officielle (table_rating_categorie.xlsx) : importance -> note par rating 1..13
TABLE = {
    "A": [40, 45, 50, 55, 60, 65, 70, 75, 79, 83, 87, 91, 95],
    "B": [35, 40, 45, 50, 55, 60, 65, 70, 74, 78, 82, 86, 90],
    "C": [25, 30, 35, 40, 45, 50, 55, 60, 64, 68, 72, 76, 80],
    "D": [15, 20, 25, 30, 35, 40, 45, 50, 54, 58, 62, 66, 70],
}

POIDS = {"A": 0.5, "B": 0.25, "C": 0.15, "D": 0.10}

# Taxonomie officielle (Poids_par_poste.xlsx), complétée :
# Leadership en D pour pilier g/d, n°4, n°5, flanker, centres, ailier ;
# Acceleration en B pour les centres.
TAXONOMIE = {
    "pilier gauche": {
        "A": ["Scrum", "Strength", "Rucking", "Tenacity", "Aggression"],
        "B": ["Power", "Positioning", "Line Out", "Tackling"],
        "C": ["Composure", "Stamina"],
        "D": ["Acceleration", "Speed", "Skill", "Leadership"],
        "0": ["Positional Kicking", "Goal Kick", "Creativity"],
    },
    "talonneur": {
        "A": ["Line Out", "Scrum", "Leadership", "Strength", "Rucking"],
        "B": ["Power", "Positioning", "Composure", "Tenacity", "Tackling", "Aggression"],
        "C": ["Stamina"],
        "D": ["Acceleration", "Speed", "Skill"],
        "0": ["Positional Kicking", "Goal Kick", "Creativity"],
    },
    "pilier droit": {
        "A": ["Power", "Strength", "Rucking", "Scrum", "Aggression"],
        "B": ["Positioning", "Line Out", "Tenacity", "Tackling"],
        "C": ["Composure", "Stamina"],
        "D": ["Acceleration", "Speed", "Skill", "Leadership"],
        "0": ["Positional Kicking", "Goal Kick", "Creativity"],
    },
    "numero 4": {
        "A": ["Strength", "Rucking", "Line Out", "Tenacity", "Aggression"],
        "B": ["Power", "Positioning", "Scrum", "Tackling"],
        "C": ["Composure", "Stamina"],
        "D": ["Acceleration", "Speed", "Skill", "Leadership"],
        "0": ["Positional Kicking", "Goal Kick", "Creativity"],
    },
    "numero 5": {
        "A": ["Power", "Strength", "Rucking", "Scrum", "Aggression"],
        "B": ["Positioning", "Line Out", "Tenacity", "Tackling"],
        "C": ["Composure", "Stamina"],
        "D": ["Acceleration", "Speed", "Skill", "Leadership"],
        "0": ["Positional Kicking", "Goal Kick", "Creativity"],
    },
    "flanker 6/7": {
        "A": ["Strength", "Rucking", "Line Out", "Tenacity", "Tackling", "Aggression"],
        "B": ["Power", "Positioning"],
        "C": ["Acceleration", "Speed", "Scrum", "Composure", "Skill", "Stamina"],
        "D": ["Creativity", "Leadership"],
        "0": ["Positional Kicking", "Goal Kick"],
    },
    "numero 8": {
        "A": ["Power", "Strength", "Leadership", "Rucking", "Line Out", "Tenacity", "Aggression"],
        "B": ["Positioning", "Scrum", "Tackling"],
        "C": ["Acceleration", "Speed", "Composure", "Skill", "Stamina"],
        "D": ["Creativity"],
        "0": ["Positional Kicking", "Goal Kick"],
    },
    "demi de melee": {
        "A": ["Leadership", "Acceleration", "Positional Kicking", "Creativity", "Skill"],
        "B": ["Speed", "Positioning", "Goal Kick", "Composure", "Stamina"],
        "C": ["Power", "Tenacity", "Tackling"],
        "D": ["Strength", "Aggression"],
        "0": ["Rucking", "Line Out", "Scrum"],
    },
    "demi douverture": {
        "A": ["Leadership", "Acceleration", "Positional Kicking", "Goal Kick", "Composure", "Creativity", "Skill"],
        "B": ["Speed", "Positioning", "Stamina"],
        "C": ["Power", "Tenacity", "Tackling"],
        "D": ["Strength", "Aggression"],
        "0": ["Rucking", "Line Out", "Scrum"],
    },
    "premier centre": {
        "A": ["Power", "Positioning", "Tackling", "Skill"],
        "B": ["Strength", "Speed", "Creativity", "Stamina", "Acceleration"],
        "C": ["Positional Kicking", "Composure", "Tenacity", "Aggression"],
        "D": ["Rucking", "Leadership"],
        "0": ["Goal Kick", "Line Out", "Scrum"],
    },
    "deuxieme centre": {
        "A": ["Power", "Speed", "Positioning", "Tackling"],
        "B": ["Strength", "Creativity", "Skill", "Stamina", "Acceleration"],
        "C": ["Positional Kicking", "Composure", "Tenacity", "Aggression"],
        "D": ["Rucking", "Leadership"],
        "0": ["Goal Kick", "Line Out", "Scrum"],
    },
    "ailier": {
        "A": ["Acceleration", "Speed", "Skill", "Stamina"],
        "B": ["Positioning", "Composure"],
        "C": ["Power", "Positional Kicking", "Tenacity", "Creativity"],
        "D": ["Strength", "Tackling", "Aggression", "Leadership"],
        "0": ["Rucking", "Goal Kick", "Line Out", "Scrum"],
    },
    "arriere": {
        "A": ["Leadership", "Acceleration", "Speed", "Positional Kicking", "Positioning", "Skill", "Stamina"],
        "B": ["Goal Kick", "Composure", "Tackling", "Creativity"],
        "C": ["Power", "Tenacity"],
        "D": ["Strength", "Aggression"],
        "0": ["Rucking", "Line Out", "Scrum"],
    },
}

# Familles de secteurs pour le moteur (avants / charnière / lignes arrière)
FAMILLES = {
    "pilier gauche": "avant", "talonneur": "avant", "pilier droit": "avant",
    "numero 4": "avant", "numero 5": "avant", "flanker 6/7": "avant", "numero 8": "avant",
    "demi de melee": "charniere", "demi douverture": "charniere",
    "premier centre": "arriere", "deuxieme centre": "arriere",
    "ailier": "arriere", "arriere": "arriere",
}


class Joueur:
    def __init__(self, poste, rating, notes, rng_nom=None):
        self.poste = poste
        self.rating = rating
        self.notes = notes

    def moyenne_generale(self):
        """M = PartieEntière[(0.5*MoyA + 0.25*MoyB + 0.15*MoyC + 0.10*MoyD)
        renormalisée par les poids présents + 5]."""
        taxo = TAXONOMIE[self.poste]
        somme, poids_total = 0.0, 0.0
        for cat, poids in POIDS.items():
            attrs = taxo[cat]
            if not attrs:
                continue
            somme += poids * (sum(self.notes[a] for a in attrs) / len(attrs))
            poids_total += poids
        return int(somme / poids_total + 5)

    def famille(self):
        return FAMILLES[self.poste]

    def __str__(self):
        m = self.moyenne_generale()
        return f"{self.poste} (rating {self.rating}) : M = {m}"


def generer_notes(poste, rating, rng=None):
    """Génère les 18 notes du joueur : table + bruit uniforme [-5, +5],
    bornes [0, 99]. Les attributs non avenues restent à 0."""
    rng = rng or random
    taxo = TAXONOMIE[poste]
    notes = {a: 0 for a in ATTRIBUTS}
    for cat in ("A", "B", "C", "D"):
        base = TABLE[cat][rating - 1]
        for a in taxo[cat]:
            notes[a] = max(0, min(99, base + rng.randint(-5, 5)))
    return notes


def generer_joueur(poste, rating, rng=None):
    notes = generer_notes(poste, rating, rng)
    return Joueur(poste, rating, notes)


def tirer_rating(rng, minimum=1, maximum=13, base=0.4):
    """Distribution exponentielle : l'entonnoir du rugby mondial, beaucoup
    d'amateurs (1-5), quelques world class (12-13)."""
    rng = rng or random
    rating = 1
    while rating < maximum and rng.random() < base:
        rating += 1
    return max(minimum, min(maximum, rating))


if __name__ == "__main__":
    rng = random.Random(2026)
    print("=== Vérification des moyennes M par rating (100 joueurs/poste) ===")
    for rating in (6, 9, 11, 12, 13):
        moyennes = []
        for poste in TAXONOMIE:
            ms = [generer_joueur(poste, rating, rng).moyenne_generale() for _ in range(100)]
            moyennes += ms
        print(f"  Rating {rating}: M moyenne {sum(moyennes)/len(moyennes):.1f} "
              f"(min {min(moyennes)}, max {max(moyennes)})")

    print("\n=== Exemples de joueurs ===")
    for poste, rating in [("pilier droit", 12), ("demi douverture", 12), ("numero 8", 11), ("ailier", 7)]:
        j = generer_joueur(poste, rating, rng)
        tri = sorted(j.notes.items(), key=lambda x: -x[1])
        print(f"\n{poste} (rating {rating}) : M = {j.moyenne_generale()}")
        for a, v in tri:
            if v > 0:
                print(f"    {a:<20}{v:>3}  {'█' * int(v / 4)}")
            else:
                print(f"    {a:<20}  0  (non avenue)")
