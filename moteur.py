# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 20:02:09 2026

@author: gabri
"""

import random
from dataclasses import dataclass, field



VALEUR_CALIBRE = {
    "World Class": 98,
    "International": 90,
    "National": 80,
    "Pro": 70,
    "Semi-Pro": 60,
    "Amateur": 50
}


@dataclass
class Cartons:
    jaunes: list = field(default_factory=list)
    rouge: bool = False
    fautes_consecutives: int = 0
    count_jaune: int = 0
    count_rouge: int = 0


@dataclass
class Stats:
    essais_a: int = 0
    essais_b: int = 0
    penalites_a: int = 0
    penalites_b: int = 0
    drops_a: int = 0
    drops_b: int = 0
    jaunes_a: int = 0
    jaunes_b: int = 0
    rouges_a: int = 0
    rouges_b: int = 0


@dataclass
class Match:
    nom_a: str
    nom_b: str
    forme_a: float
    forme_b: float
    temps: int = 0
    score_a: int = 0
    score_b: int = 0
    stats: Stats = field(default_factory=Stats)
    cartons_a: Cartons = field(default_factory=Cartons)
    cartons_b: Cartons = field(default_factory=Cartons)
    journal: list = field(default_factory=list)

    def log(self, message):
        self.journal.append(f"[{self.temps}'] {message}")


def calculer_force_equipe(effectif_40):
    """
    effectif_40: dictionnaire { "Calibre": nombre_de_joueurs }
    Exemple: {"World Class": 2, "International": 5, ...}
    """
    liste_notes = []
    for calibre, quantite in effectif_40.items():
        liste_notes.extend([VALEUR_CALIBRE[calibre]] * quantite)

    liste_notes.sort(reverse=True)

    top_23 = liste_notes[:23]
    reservistes = liste_notes[23:]
    

    moyenne_top23 = sum(top_23) / len(top_23)
    
    moyenne_reservistes = sum(reservistes) / len(reservistes) if reservistes else 0

    force_base = (moyenne_top23)*0.8 + (moyenne_reservistes)*0.2
    return force_base


def choisir_action_penalite(ecart_score, temps, essais_att, essais_def):
    """
    Détermine si l'équipe tente les 3 points ou va en pénaltouche selon le contexte du match.
    ecart_score = score_attaquant - score_defenseur
    """
    
    # --- FIN DE MATCH (Minute 70+) ---
    if temps >= 70:
        if ecart_score <= -11:
            return "PENALTOUCHE"
        if -10 <= ecart_score <= -8:
            return "PENALITE"
        if -7 <= ecart_score <= -4:
            return "PENALTOUCHE"
        if -3 <= ecart_score <= 0:
            return "PENALITE"
        if 1 <= ecart_score <= 5:
            return "PENALITE"

    # --- CHASSE AU BONUS OFFENSIF ---
    if temps >= 65 and (essais_att - essais_def) == 2 and ecart_score > 7:
        return "PENALTOUCHE"
    elif temps >= 50 and (essais_att - essais_def) == 2:
        if random.random() < 0.60:
            return "PENALTOUCHE"
    elif temps >= 50 and ecart_score >= -18:
        return "PENALTOUCHE"
    elif (essais_att - essais_def) == 2:
        if random.random() < 0.50:
            return "PENALTOUCHE"

    # --- COMPORTEMENT PAR DÉFAUT (75% pénalité / 25% pénaltouche) ---
    return "PENALITE" if random.random() < 0.75 else "PENALTOUCHE"


def initialiser_match(equipe_a_40, equipe_b_40, nom_a, nom_b, avantage_domicile=True, avantage_demi=False):
    bonus_dom = 6 if avantage_domicile else 0
    bonus_demi = 3 if avantage_demi else 0
    forme_a = calculer_force_equipe(equipe_a_40) + bonus_dom + bonus_demi
    forme_b = calculer_force_equipe(equipe_b_40)
    return Match(nom_a=nom_a, nom_b=nom_b, forme_a=forme_a, forme_b=forme_b)


def maj_chrono_jaunes(match, cartons, nom, duree):
    if not cartons.jaunes:
        return
    cartons.jaunes = [max(0, t - duree) for t in cartons.jaunes]
    cartons.jaunes = [t for t in cartons.jaunes if t > 0]
    cartons.count_jaune = len(cartons.jaunes)
    if not cartons.jaunes and not cartons.rouge:
        match.log(f"{nom} est de nouveau au complet (Fin du carton jaune).")


def forme_effective(forme, cartons):
    malus = 0.05 * (cartons.count_jaune + cartons.count_rouge) ** 2
    return forme * (1 - malus)


def ajouter_essai(match, est_a, message):
    points = 5 + (2 if random.random() < 0.75 else 0)
    if est_a:
        match.score_a += points
        match.stats.essais_a += 1
    else:
        match.score_b += points
        match.stats.essais_b += 1
    match.log(f"{message} ({match.score_a} - {match.score_b})")


def tenter_penalite(match, est_a):
    nom_att = match.nom_a if est_a else match.nom_b
    if random.random() < 0.80:
        if est_a:
            match.score_a += 3
            match.stats.penalites_a += 1
        else:
            match.score_b += 3
            match.stats.penalites_b += 1
        match.log(f"Pénalité réussie par {nom_att}. ({match.score_a} - {match.score_b})")
    else:
        match.log(f"Pénalité manquée par {nom_att} ! ({match.score_a} - {match.score_b})")


def tenter_drop(match, est_a):
    """
    Tente un drop en jeu ouvert si le contexte de score l'incite :
    l'équipe est menée de 3 points ou moins, ou mène de 7 points ou moins.
    Retourne True si un drop a été tenté.
    """
    score_att = match.score_a if est_a else match.score_b
    score_def = match.score_b if est_a else match.score_a
    ecart_score = score_att - score_def

    if not (-3 <= ecart_score <= 7):
        return False


    nom_att = match.nom_a if est_a else match.nom_b
    if est_a:
        match.score_a += 3
        match.stats.drops_a += 1
    else:
        match.score_b += 3
        match.stats.drops_b += 1
    match.log(f"DROP claqué par {nom_att} ! ({match.score_a} - {match.score_b})")
    return True


def tirer_sanction(match, est_a, cartons_def):
    score_att = match.score_a if est_a else match.score_b
    score_def = match.score_b if est_a else match.score_a
    essais_att = match.stats.essais_a if est_a else match.stats.essais_b
    essais_def = match.stats.essais_b if est_a else match.stats.essais_a

    ecart_score = score_att - score_def
    action = choisir_action_penalite(ecart_score, match.temps, essais_att, essais_def)

    if action == "PENALITE":
        tenter_penalite(match, est_a)
        match.temps += 1
    else:
        nom_att = match.nom_a if est_a else match.nom_b
        taux_conversion = 0.55 if (cartons_def.jaunes or cartons_def.rouge) else 0.40
        if random.random() < taux_conversion:
            ajouter_essai(match, est_a, f"{nom_att} va en pénaltouche... et marque un ESSAI !")
        else:
            match.log(f"{nom_att} va en pénaltouche... mais perd le ballon ! ({match.score_a} - {match.score_b})")
        match.temps +=1
            

def donner_carton_jaune(match, est_a):
    fautif = match.nom_b if est_a else match.nom_a
    cartons_def = match.cartons_b if est_a else match.cartons_a
    cartons_def.jaunes.append(10)
    cartons_def.count_jaune += 1
    if fautif == match.nom_a:
        match.stats.jaunes_a += 1
    else:
        match.stats.jaunes_b += 1
    A = random.random()
    if A<0.4:
        match.log(f"🟨 CARTON JAUNE contre {fautif} ! Antijeu.")
    elif A<0.8:
        match.log(f"🟨 Placage haut sanctionné d'un CARTON JAUNE pour {fautif} !")
    else:
        match.log(f"🟨 En-avant volontaire de {fautif} ! CARTON JAUNE.")
    tirer_sanction(match, est_a, cartons_def)
    
    
def donner_carton_rouge(match, est_a):
    fautif = match.nom_b if est_a else match.nom_a
    cartons_def = match.cartons_b if est_a else match.cartons_a
    cartons_def.rouge = True
    cartons_def.count_rouge += 1
    if fautif == match.nom_a:
        match.stats.rouges_a += 1
    else:
        match.stats.rouges_b += 1
    match.log(f"🔴 CARTON ROUGE pour {fautif} ! Jeu déloyal avec degré de danger elevé.")
    tirer_sanction(match, est_a, cartons_def)


def sanctionner_faute(match, est_a):
    cartons_def = match.cartons_b if est_a else match.cartons_a
    cartons_att = match.cartons_a if est_a else match.cartons_b
    nom_def = match.nom_b if est_a else match.nom_a
    # La pression s'inverse : l'attaquant qui obtient la pénalité
    # est délivré de ses fautes accumulées en défense.
    cartons_att.fautes_consecutives = 0
    cartons_def.fautes_consecutives += 1

    if cartons_def.fautes_consecutives >= 3:
        cartons_def.jaunes.append(10)
        cartons_def.count_jaune += 1
        cartons_def.fautes_consecutives = 0
        if est_a:
            match.stats.jaunes_b += 1
        else:
            match.stats.jaunes_a += 1
        match.log(f"🟨 CARTON JAUNE contre {nom_def} pour une accumulation de fautes !")

    tirer_sanction(match, est_a, cartons_def)


def simuler_action(match):
    duree = random.randint(1, 3)
    match.temps += duree

    maj_chrono_jaunes(match, match.cartons_a, match.nom_a, duree)
    maj_chrono_jaunes(match, match.cartons_b, match.nom_b, duree)

    forme_a = forme_effective(match.forme_a, match.cartons_a)
    forme_b = forme_effective(match.forme_b, match.cartons_b)
    prob_domination_a = forme_a / (forme_a + forme_b)

    est_a = random.random() < prob_domination_a
    delta = (forme_a - forme_b) if est_a else (forme_b - forme_a)

    #chance_essai = max(0.05, 0.12 + (delta * 0.004))
    #chance_penalite = max(0.10, 0.20 + (delta * 0.003))
    chance_essai = max(0.075, 0.14 + (delta * 0.005))
    chance_penalite = max(0.11, 0.22 + (delta * 0.0033))
    chance_rouge = 0.003
    chance_jaune = 0.03
    chance_drop = 0.0000001*(match.temps)**3

    tirage = random.random()
    if tirage < chance_rouge:
        donner_carton_rouge(match, est_a)
    elif tirage < (chance_rouge + chance_jaune):
        donner_carton_jaune(match, est_a)
    elif tirage < (chance_rouge + chance_jaune + chance_essai):
        match.cartons_a.fautes_consecutives = 0
        match.cartons_b.fautes_consecutives = 0
        nom_att = match.nom_a if est_a else match.nom_b
        ajouter_essai(match, est_a, f"ESSAI pour {nom_att} !")
        match.temps += 1
    elif tirage < (chance_rouge + chance_jaune + chance_essai + chance_penalite):
        sanctionner_faute(match, est_a)
    elif tirage < (chance_rouge + chance_jaune + chance_essai + chance_penalite + chance_drop):
        tenter_drop(match, est_a)


def conclure_match(match):
    s = match.stats
    match.journal.append("")
    match.journal.append("=== SCORE FINAL ===")
    match.journal.append(f"{match.nom_a} {match.score_a} - {match.score_b} {match.nom_b}")
    match.journal.append(f"Détails {match.nom_a}: {s.essais_a} essai(s), {s.penalites_a} pénalité(s), {s.drops_a} drop(s), {s.jaunes_a} jaune(s), {s.rouges_a} rouge(s)")
    match.journal.append(f"Détails {match.nom_b}: {s.essais_b} essai(s), {s.penalites_b} pénalité(s), {s.drops_b} drop(s), {s.jaunes_b} jaune(s), {s.rouges_b} rouge(s)")


def afficher_journal(match):
    for ligne in match.journal:
        print(ligne)


def simuler_match(equipe_a_40, equipe_b_40, nom_a="Équipe A", nom_b="Équipe B", avantage_domicile=True, avantage_demi=False):
    match = initialiser_match(equipe_a_40, equipe_b_40, nom_a, nom_b, avantage_domicile=avantage_domicile, avantage_demi=avantage_demi)
    match.journal.append(f"Le {nom_a} ({match.forme_a:.1f}) reçoit le {nom_b} ({match.forme_b:.1f}) !")
    match.journal.append("--- DÉBUT DU MATCH ---")

    mi_temps_affiche = False
    while match.temps < 80:
        if match.temps >= 40 and not mi_temps_affiche:
            match.journal.append("--- MI-TEMPS ---")
            mi_temps_affiche = True
        simuler_action(match)

    conclure_match(match)
    return match


# # Équipe 1 : Effectif très compétitif (Top de tableau)
# equipe_elite = {
#     "World Class": 3,
#     "International": 7,
#     "National": 12,
#     "Pro": 10,
#     "Semi-Pro": 5,
#     "Amateur": 3
# }

# equipe_elite_2 = {
#     "World Class": 3,
#     "International": 7,
#     "National": 12,
#     "Pro": 10,
#     "Semi-Pro": 5,
#     "Amateur": 3
# }

# # Équipe 2 : Effectif intermédiaire
# equipe_moyenne = {
#     "World Class": 0,
#     "International": 2,
#     "National": 8,
#     "Pro": 18,
#     "Semi-Pro": 8,
#     "Amateur": 4
# }

# Mont2 = {
#     "World Class": 0,
#     "International": 0,
#     "National": 0,
#     "Pro": 35,
#     "Semi-Pro": 5,
#     "Amateur": 0
# }

# Tarbes = {
#     "World Class": 0,
#     "International": 0,
#     "National": 0,
#     "Pro": 2,
#     "Semi-Pro": 38,
#     "Amateur": 0
# }

# SOC = {
#     "World Class": 0,
#     "International": 0,
#     "National": 4,
#     "Pro": 35,
#     "Semi-Pro": 1,
#     "Amateur": 0
# }

CAB = {
    "World Class": 0,
    "International": 0,
    "National": 8,
    "Pro": 32,
    "Semi-Pro": 0,
    "Amateur": 0
}


Seawolves = {
    "World Class": 0,
    "International": 0,
    "National": 4,
    "Pro": 21,
    "Semi-Pro": 15,
    "Amateur": 0
}

Chile = {
    "World Class": 0,
    "International": 1,
    "National": 15,
    "Pro": 7,
    "Semi-Pro": 0,
    "Amateur": 0
}

Penarol = {
    "World Class": 0,
    "International": 0, 
    "National": 8, 
    "Pro": 25, 
    "Semi-Pro": 7, 
    "Amateur": 0}

AFS = {
    "World Class": 13,
    "International": 10,
    "National": 0,
    "Pro": 0,
    "Semi-Pro": 0,
    "Amateur": 0
}

France = {
    "World Class": 10,
    "International": 10,
    "National": 3,
    "Pro": 0,
    "Semi-Pro": 0,
    "Amateur": 0
}

Castres =       {"World Class": 0, 
                      "International": 4,  
                      "National": 18, 
                      "Pro": 18}

# Lancer la simulation

match = simuler_match(Seawolves, Penarol, "Seattle", "Penarol", avantage_domicile=True, avantage_demi=False)
afficher_journal(match)



#si l'équipe est d'un calibre très supérieur, elle ira systématiquement en penaltouche
#équilibre entre avant-3/4-charnière
#avant : avoir le ballon, dominer l'adversaire --> pourcentage de possession +++, chance de penalité +++, chance de marquer +
#charnière : réussite au pied et transformation du jeu --> taux de reussite, pourcentage de possession ++, chance de pénalité ++, chance de marquer ++
#arrière : efficacité du jeu de ligne --> pourcentage de possession +, chance de pénalité +, chance de marquer +++