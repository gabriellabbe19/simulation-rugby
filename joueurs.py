# -*- coding: utf-8 -*-
"""
Module joueurs : fiches individuelles, matrice de poids par poste,
générateur de notes calibré sur le dataset PlayersAnalysis.csv.

Postes du jeu (Primary Position) -> poste standardisé 1-15 :
  Loosehead Prop=1, Hooker=2, Tighthead Prop=3, Lock=4/5, Flanker=6/7,
  Number 8=8, Scrum Half=9, Fly Half=10, Inside Centre=12,
  Outside Centre=13, Wing=11/14, Full Back=15, Utility Back=arrière polyvalent
"""

import csv
import os
import random
import statistics as st
from dataclasses import dataclass, field

ATTRIBUTS = [
    # Physique
    "Acceleration", "Power", "Skill", "Speed", "Stamina", "Strength",
    # Mental
    "Aggression", "Composure", "Creativity", "Leadership", "Positioning", "Tenacity",
    # Technique
    "Goal Kick", "Line Out", "Scrum", "Rucking", "Positional Kicking", "Tackling",
]

# Correspondance poste joueur -> famille de secteurs (pour le moteur)
FAMILLES = {
    "Loosehead Prop": "avant", "Hooker": "avant", "Tighthead Prop": "avant",
    "Lock": "avant", "Flanker": "avant", "Number 8": "avant",
    "Scrum Half": "charniere", "Fly Half": "charniere",
    "Inside Centre": "arriere", "Outside Centre": "arriere",
    "Wing": "arriere", "Full Back": "arriere", "Utility Back": "arriere",
}

# Matrice de poids : note -> {poste: poids}, corrigée d'après les moyennes
# mesurées sur 8777 joueurs du jeu. Chaque poste somme à 1.00.
MATRICE_POIDS = {
    "Loosehead Prop": {
        "Scrum": 0.22, "Strength": 0.16, "Power": 0.12, "Aggression": 0.09,
        "Rucking": 0.10, "Tackling": 0.08, "Stamina": 0.06, "Tenacity": 0.05,
        "Positioning": 0.04, "Composure": 0.03, "Leadership": 0.03,
        "Acceleration": 0.01, "Speed": 0.01, "Skill": 0.02, "Line Out": 0.00,
        "Creativity": 0.00, "Goal Kick": 0.00, "Positional Kicking": 0.00,
    },
    "Hooker": {
        "Line Out": 0.20, "Scrum": 0.14, "Strength": 0.10, "Power": 0.08,
        "Rucking": 0.10, "Tackling": 0.08, "Aggression": 0.07, "Stamina": 0.06,
        "Tenacity": 0.05, "Positioning": 0.04, "Leadership": 0.05,
        "Composure": 0.03, "Skill": 0.02, "Acceleration": 0.00, "Speed": 0.00,
        "Creativity": 0.00, "Goal Kick": 0.00, "Positional Kicking": 0.00,
    },
    "Tighthead Prop": {
        "Scrum": 0.24, "Strength": 0.16, "Power": 0.12, "Aggression": 0.09,
        "Rucking": 0.10, "Tackling": 0.08, "Stamina": 0.06, "Tenacity": 0.05,
        "Positioning": 0.04, "Composure": 0.03, "Leadership": 0.02,
        "Acceleration": 0.01, "Speed": 0.01, "Skill": 0.02, "Line Out": 0.00,
        "Creativity": 0.00, "Goal Kick": 0.00, "Positional Kicking": 0.00,
    },
    "Lock": {
        "Line Out": 0.18, "Power": 0.14, "Strength": 0.12, "Rucking": 0.10,
        "Aggression": 0.08, "Tackling": 0.08, "Tenacity": 0.06, "Stamina": 0.07,
        "Positioning": 0.05, "Composure": 0.03, "Leadership": 0.04,
        "Skill": 0.02, "Acceleration": 0.01, "Speed": 0.01,
        "Scrum": 0.01, "Creativity": 0.01, "Goal Kick": 0.00, "Positional Kicking": 0.00,
    },
    "Flanker": {
        "Tenacity": 0.15, "Aggression": 0.13, "Power": 0.11, "Rucking": 0.14,
        "Tackling": 0.11, "Stamina": 0.08, "Speed": 0.05, "Acceleration": 0.05,
        "Positioning": 0.05, "Leadership": 0.04, "Composure": 0.03,
        "Strength": 0.04, "Skill": 0.03, "Line Out": 0.02,
        "Creativity": 0.01, "Goal Kick": 0.00, "Positional Kicking": 0.00, "Scrum": 0.00,
    },
    "Number 8": {
        "Power": 0.15, "Tenacity": 0.10, "Aggression": 0.10, "Rucking": 0.10,
        "Tackling": 0.09, "Strength": 0.07, "Stamina": 0.07, "Speed": 0.05,
        "Acceleration": 0.04, "Positioning": 0.07, "Skill": 0.05,
        "Leadership": 0.06, "Composure": 0.04, "Line Out": 0.03,
        "Creativity": 0.01, "Goal Kick": 0.00, "Positional Kicking": 0.00, "Scrum": 0.00,
    },
    "Scrum Half": {
        "Acceleration": 0.14, "Skill": 0.14, "Speed": 0.07, "Creativity": 0.09,
        "Composure": 0.10, "Rucking": 0.08, "Tackling": 0.08, "Stamina": 0.07,
        "Aggression": 0.06, "Tenacity": 0.06, "Positioning": 0.06,
        "Leadership": 0.04, "Strength": 0.02, "Power": 0.02, "Positional Kicking": 0.06,
        "Goal Kick": 0.00, "Line Out": 0.00, "Scrum": 0.00,
    },
    "Fly Half": {
        "Goal Kick": 0.18, "Creativity": 0.13, "Composure": 0.10, "Skill": 0.10,
        "Positional Kicking": 0.12, "Positioning": 0.08, "Leadership": 0.05,
        "Tackling": 0.06, "Acceleration": 0.05, "Speed": 0.05, "Stamina": 0.05,
        "Tenacity": 0.02, "Aggression": 0.00, "Strength": 0.01, "Power": 0.01,
        "Rucking": 0.00, "Line Out": 0.00, "Scrum": 0.00,
    },
    "Inside Centre": {
        "Skill": 0.14, "Positioning": 0.12, "Tackling": 0.13, "Power": 0.11,
        "Composure": 0.08, "Creativity": 0.08, "Speed": 0.08, "Acceleration": 0.07,
        "Stamina": 0.06, "Tenacity": 0.06, "Aggression": 0.04, "Strength": 0.04,
        "Leadership": 0.03, "Positional Kicking": 0.02, "Goal Kick": 0.00,
        "Line Out": 0.00, "Scrum": 0.00, "Rucking": 0.00,
    },
    "Outside Centre": {
        "Tackling": 0.14, "Positioning": 0.13, "Speed": 0.10, "Skill": 0.11,
        "Acceleration": 0.09, "Composure": 0.07, "Creativity": 0.07, "Power": 0.08,
        "Stamina": 0.06, "Tenacity": 0.05, "Aggression": 0.04, "Strength": 0.03,
        "Leadership": 0.02, "Positional Kicking": 0.02, "Goal Kick": 0.00,
        "Line Out": 0.00, "Scrum": 0.00, "Rucking": 0.00,
    },
    "Wing": {
        "Speed": 0.18, "Acceleration": 0.14, "Skill": 0.12, "Stamina": 0.08,
        "Tackling": 0.08, "Positioning": 0.08, "Composure": 0.07, "Creativity": 0.07,
        "Tenacity": 0.05, "Aggression": 0.04, "Positional Kicking": 0.04,
        "Strength": 0.02, "Leadership": 0.01, "Power": 0.03, "Stamina2": 0.00,
        "Goal Kick": 0.00, "Line Out": 0.00, "Scrum": 0.00, "Rucking": 0.00,
    },
    "Full Back": {
        "Tackling": 0.12, "Stamina": 0.11, "Positioning": 0.12, "Positional Kicking": 0.12,
        "Speed": 0.09, "Skill": 0.09, "Acceleration": 0.08, "Composure": 0.09,
        "Creativity": 0.07, "Goal Kick": 0.05, "Tenacity": 0.04, "Power": 0.02,
        "Aggression": 0.00, "Strength": 0.01, "Leadership": 0.02,
        "Line Out": 0.00, "Scrum": 0.00, "Rucking": 0.00,
    },
    "Utility Back": {
        "Tackling": 0.12, "Speed": 0.11, "Skill": 0.11, "Stamina": 0.10,
        "Positioning": 0.11, "Acceleration": 0.09, "Composure": 0.08, "Creativity": 0.08,
        "Tenacity": 0.05, "Positional Kicking": 0.05, "Aggression": 0.04,
        "Power": 0.03, "Leadership": 0.03, "Goal Kick": 0.02,
        "Strength": 0.01, "Line Out": 0.00, "Scrum": 0.00, "Rucking": 0.00,
    },
}


@dataclass
class Joueur:
    nom: str
    prenom: str
    poste: str            # Primary Position du jeu
    age: int
    nationalite: str
    notes: dict           # {attribut: valeur 10-99}
    calibre: str          # Calibre du jeu (World Class, International, ...)
    rating_jeu: int       # 1 To 13 Rating
    pl: int               # Potential Left

    def note_generale(self):
        """Note générale = somme pondérée selon la matrice du poste."""
        poids = MATRICE_POIDS[self.poste]
        return sum(poids[a] * self.notes[a] for a in ATTRIBUTS)

    def note_ajustee(self, moyennes_poste=None):
        """Note pondérée normalisée : retire le biais de poste (un pilier et un
        ouvreur de même rating doivent avoir des notes comparables).
        moyennes_poste : dict {poste: note pondérée moyenne du dataset} ;
        calculé paresseusement depuis le CSV si absent."""
        if moyennes_poste is None:
            moyennes_poste = moyennes_poste_dataset()
        return self.note_generale() - moyennes_poste[self.poste] + 60.0

    def famille(self):
        return FAMILLES[self.poste]

    def __str__(self):
        return (f"{self.prenom} {self.nom} ({self.poste}, {self.age} ans, "
                f"{self.nationalite}) : note ajustée {self.note_ajustee():.1f} "
                f"[calibre {self.calibre}, rating {self.rating_jeu}, PL {self.pl}]")


_MOYENNES_POSTE = None


def moyennes_poste_dataset(chemin_csv=None):
    """Note pondérée moyenne par poste sur l'ensemble du dataset (référence
    pour la normalisation des notes entre postes)."""
    global _MOYENNES_POSTE
    if _MOYENNES_POSTE is None:
        chemin = chemin_csv or os.path.join(os.path.dirname(__file__), "PlayersAnalysis.csv")
        js = charger_joueurs_csv(chemin)
        par_poste = {}
        for j in js:
            par_poste.setdefault(j.poste, []).append(j.note_generale())
        _MOYENNES_POSTE = {p: st.mean(v) for p, v in par_poste.items()}
    return _MOYENNES_POSTE


def charger_joueurs_csv(chemin="PlayersAnalysis.csv"):
    """Charge les fiches du dataset. Retourne une liste de Joueur."""
    joueurs = []
    with open(chemin, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if not r["Primary Position"]:
                continue
            notes = {a: int(r[a]) for a in ATTRIBUTS}
            joueurs.append(Joueur(
                nom=r["Surname"], prenom=r["Forename"],
                poste=r["Primary Position"], age=int(r["Age Yrs"]),
                nationalite=r["Nationality"], notes=notes,
                calibre=r["Calibre"], rating_jeu=int(r["1 To 13 Rating"]),
                pl=int(r["Potential Left (PL)"]),
            ))
    return joueurs


# ---------------------------------------------------------------------------
# Générateur de fiches calibré sur les distributions réelles
# ---------------------------------------------------------------------------

def _distributions(joueurs):
    """Moyenne et écart-type de chaque attribut par poste (mesurés)."""
    par_poste = {}
    for j in joueurs:
        par_poste.setdefault(j.poste, []).append(j)
    dist = {}
    for poste, js in par_poste.items():
        dist[poste] = {
            a: (st.mean([j.notes[a] for j in js]),
                st.pstdev([j.notes[a] for j in js]))
            for a in ATTRIBUTS
        }
    return dist


_DISTRIBUTIONS = None


def distributions(chemin_csv=None, joueurs=None):
    """Lazy : charge le CSV une fois, calcule les stats par poste."""
    global _DISTRIBUTIONS
    if _DISTRIBUTIONS is None:
        chemin = chemin_csv or os.path.join(os.path.dirname(__file__), "PlayersAnalysis.csv")
        js = joueurs or charger_joueurs_csv(chemin)
        _DISTRIBUTIONS = _distributions(js)
    return _DISTRIBUTIONS


def generer_joueur(poste, calibre, rng=None, nom="", prenom="", age=25, nationalite="France"):
    """Génère une fiche complète en tirant chaque note dans la loi normale
    empirique du poste (moyenne ± écart-type mesurés), bornée [10, 99].
    Le calibre module le tirage : World Class au-dessus de la moyenne, etc.
    """
    rng = rng or random
    dist = distributions()[poste]
    RATING_CALIBRE = {
        "World Class": 12, "International": 11, "National": 10,
        "Pro": 9, "Professional": 9, "Semi-Pro": 7, "Amateur": 6,
    }
    rating_cible = RATING_CALIBRE[calibre]
    notes = {}
    for a in ATTRIBUTS:
        moy, sigma = dist[a]
        # Le calibre décale la loi : environ +4 par cran de rating au-dessus
        # de la moyenne du dataset (moyenne de rating ~7.5).
        decalage = (rating_cible - 7.5) * 4
        tirage = rng.gauss(moy + decalage, sigma)
        notes[a] = int(max(10, min(99, round(tirage))))
    return Joueur(
        nom=nom, prenom=prenom, poste=poste, age=age,
        nationalite=nationalite, notes=notes, calibre=calibre,
        rating_jeu=rating_cible, pl=0,
    )


if __name__ == "__main__":
    joueurs = charger_joueurs_csv()
    print(f"{len(joueurs)} joueurs chargés.")
    rng = random.Random(42)
    for poste in ["Tighthead Prop", "Fly Half", "Scrum Half", "Wing"]:
        j = generer_joueur(poste, "International", rng)
        top = sorted(j.notes.items(), key=lambda x: -x[1])[:4]
        print(f"\n{poste} (International) :")
        for a, v in top:
            print(f"    {a:<20}{v}")
        print(f"    -> note générale pondérée : {j.note_generale():.1f} | ajustée (réf. 60) : {j.note_ajustee():.1f}")
