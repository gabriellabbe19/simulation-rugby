# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 00:02:37 2026

@author: gabri
"""

import random
from dataclasses import dataclass, field

from moteur import simuler_match


EFFECTIFS_TOP14 = {
    "Toulouse":          {"World Class": 4, "International": 12, "National": 16, "Pro": 8},
    "Bordeaux Bègles":   {"World Class": 3, "International": 10, "National": 17, "Pro": 10},
    "Stade Français":    {"World Class": 1, "International": 7,  "National": 18, "Pro": 14},
    "Racing 92":         {"World Class": 1, "International": 6,  "National": 18, "Pro": 15},
    "La Rochelle":       {"World Class": 2, "International": 8,  "National": 18, "Pro": 12},
    "Clermont":          {"World Class": 1, "International": 6,  "National": 18, "Pro": 15},
    "Castres":           {"World Class": 0, "International": 4,  "National": 18, "Pro": 18},
    "Pau":               {"World Class": 1, "International": 7,  "National": 17, "Pro": 15},
    "Toulon":            {"World Class": 1, "International": 6,  "National": 18, "Pro": 15},
    "Lyon":              {"World Class": 1, "International": 5,  "National": 18, "Pro": 16},
    "Montpellier":       {"World Class": 0, "International": 4,  "National": 18, "Pro": 18},
    "Perpignan":         {"World Class": 0, "International": 3,  "National": 17, "Pro": 20},
    "Bayonne":           {"World Class": 0, "International": 3,  "National": 17, "Pro": 20},
    "Vannes":            {"World Class": 0, "International": 1,  "National": 12, "Pro": 27},
}



    
@dataclass
class ResultatMatch:
    journee: int
    domicile: str
    exterieur: str
    score_dom: int
    score_ext: int
    essais_dom: int
    essais_ext: int
    penalites_dom: int
    penalites_ext: int
    drops_dom: int
    drops_ext: int
    jaunes_dom: int
    jaunes_ext: int
    rouges_dom: int
    rouges_ext: int
    journal: list = field(default_factory=list)


@dataclass
class LigneClassement:
    nom: str
    joues: int = 0
    gagnes: int = 0
    nuls: int = 0
    perdus: int = 0
    points: int = 0
    bonus_off: int = 0
    bonus_def: int = 0
    essais_marques: int = 0
    essais_encaisses: int = 0
    penalites: int = 0
    drops: int = 0
    jaunes: int = 0
    rouges: int = 0
    points_marques: int = 0
    points_encaisses: int = 0

    @property
    def difference(self):
        return self.points_marques - self.points_encaisses


def _paires_aller(noms):
    """
    Méthode du cercle : 14 équipes -> 13 journées où chaque paire se rencontre une fois.
    Retourne des paires non orientées sous forme de tuples triés (déterministes).
    """
    equipes = list(noms)
    n = len(equipes)
    pivot = equipes[0]
    tournant = equipes[1:]
    journees = []
    for _ in range(n - 1):
        paires = [tuple(sorted((pivot, tournant[0])))]
        paires += [tuple(sorted((tournant[i], tournant[-i]))) for i in range(1, n // 2)]
        journees.append(paires)
        tournant = [tournant[-1]] + tournant[:-1]
    return journees


def generer_calendrier(noms):
    """
    Calendrier aller-retour réaliste :
    - 26 journées, chaque paire se rencontre 2 fois (une fois par terrain) ;
    - 13 réceptions et 13 déplacements par équipe ;
    - les matchs à domicile et à l'extérieur alternent : aucune équipe n'enchaîne
      plus de 2 matchs consécutifs sur le même terrain.

    Méthode :
    1. paires de l'aller par la méthode du cercle ;
    2. orientation gloutonne (alterner les terrains, équilibrer les réceptions) ;
    3. descente locale : on retourne l'orientation de paires pour éliminer
       toute série de 3+ terrains identiques consécutifs dans l'aller ;
    4. retour = matchs inversés, journées en ordre inverse (miroir), ce qui
       garantit aussi l'alternance à la jonction aller/retour.
    """
    equipes = list(noms)
    n = len(equipes)
    aller = _paires_aller(noms)

    # --- 1. Orientation gloutonne des 13 journées aller ---
    orientation = {}
    dernier_terrain = {}
    receptions = {nom: 0 for nom in equipes}

    for paire in aller[0]:
        x, y = paire
        orientation[paire] = x
        dernier_terrain[x] = "D"
        dernier_terrain[y] = "E"
        receptions[x] += 1

    for journee in aller[1:]:
        for paire in journee:
            x, y = paire
            cout_x = (1 if dernier_terrain.get(x) == "D" else 0) \
                + (1 if dernier_terrain.get(y) == "E" else 0) \
                + 2 * (receptions[x] - receptions[y])
            cout_y = (1 if dernier_terrain.get(y) == "D" else 0) \
                + (1 if dernier_terrain.get(x) == "E" else 0) \
                + 2 * (receptions[y] - receptions[x])
            if cout_x < cout_y or (cout_x == cout_y and receptions[x] <= receptions[y]):
                recevant = x
            else:
                recevant = y
            orientation[paire] = recevant
            autre = y if recevant == x else x
            dernier_terrain[recevant] = "D"
            dernier_terrain[autre] = "E"
            receptions[recevant] += 1

    # --- 2. Descente locale : zéro série de 3+ dans l'aller ---
    def journee_orientee(journee, inverse=False):
        matchs = []
        for paire in journee:
            recevant = orientation[paire]
            if inverse:
                recevant = paire[0] if recevant == paire[1] else paire[1]
            visiteur = paire[0] if recevant == paire[1] else paire[1]
            matchs.append((recevant, visiteur))
        return matchs

    def defauts_aller():
        total = 0
        for equipe in equipes:
            suite = []
            for journee in aller:
                for dom, ext in journee_orientee(journee):
                    if dom == equipe:
                        suite.append("D")
                    elif ext == equipe:
                        suite.append("E")
            for i in range(1, len(suite) - 1):
                if suite[i - 1] == suite[i] == suite[i + 1]:
                    total += 1
        return total

    toutes_paires = [paire for journee in aller for paire in journee]
    meilleur = defauts_aller()
    for _ in range(200):
        if meilleur == 0:
            break
        ameliore = False
        for paire in toutes_paires:
            recevant = orientation[paire]
            autre = paire[0] if recevant == paire[1] else paire[1]
            orientation[paire] = autre
            if defauts_aller() < meilleur:
                meilleur = defauts_aller()
                ameliore = True
                break
            orientation[paire] = recevant
        if not ameliore:
            break

    # --- 3. Assemblage : aller puis retour miroir (journées inversées) ---
    calendrier = [journee_orientee(j) for j in aller] \
        + [journee_orientee(j, inverse=True) for j in reversed(aller)]

    return calendrier


def stats_alternation(calendrier, noms):
    """Retourne la plus longue série consécutive sur le même terrain par équipe."""
    stats = {}
    for equipe in noms:
        suite = []
        for journee in calendrier:
            for dom, ext in journee:
                if dom == equipe:
                    suite.append("D")
                elif ext == equipe:
                    suite.append("E")
        plus_longue = 1
        courante = 1
        for i in range(1, len(suite)):
            courante = courante + 1 if suite[i] == suite[i - 1] else 1
            plus_longue = max(plus_longue, courante)
        stats[equipe] = plus_longue
    return stats


def appliquer_resultat(r, classement):
    """Met à jour les lignes de classement à partir d'un résultat enregistré."""
    dom = classement[r.domicile]
    ext = classement[r.exterieur]

    dom.joues += 1
    ext.joues += 1
    dom.essais_marques += r.essais_dom
    dom.essais_encaisses += r.essais_ext
    ext.essais_marques += r.essais_ext
    ext.essais_encaisses += r.essais_dom
    dom.penalites += r.penalites_dom
    ext.penalites += r.penalites_ext
    dom.drops += r.drops_dom
    ext.drops += r.drops_ext
    dom.jaunes += r.jaunes_dom
    ext.jaunes += r.jaunes_ext
    dom.rouges += r.rouges_dom
    ext.rouges += r.rouges_ext
    dom.points_marques += r.score_dom
    dom.points_encaisses += r.score_ext
    ext.points_marques += r.score_ext
    ext.points_encaisses += r.score_dom

    ecart = r.score_dom - r.score_ext

    if ecart > 0:
        dom.gagnes += 1
        ext.perdus += 1
        dom.points += 4
        if r.essais_dom - r.essais_ext >= 3:
            dom.points += 1
            dom.bonus_off += 1
        if ecart <= 7:
            ext.points += 1
            ext.bonus_def += 1
    elif ecart < 0:
        ext.gagnes += 1
        dom.perdus += 1
        ext.points += 4
        if r.essais_ext - r.essais_dom >= 3:
            ext.points += 1
            ext.bonus_off += 1
        if -ecart <= 7:
            dom.points += 1
            dom.bonus_def += 1
    else:
        dom.nuls += 1
        ext.nuls += 1
        dom.points += 2
        ext.points += 2


def enregistrer_resultat(match, journee, classement, resultats):
    s = match.stats

    r = ResultatMatch(
        journee=journee,
        domicile=match.nom_a,
        exterieur=match.nom_b,
        score_dom=match.score_a,
        score_ext=match.score_b,
        essais_dom=s.essais_a,
        essais_ext=s.essais_b,
        penalites_dom=s.penalites_a,
        penalites_ext=s.penalites_b,
        drops_dom=s.drops_a,
        drops_ext=s.drops_b,
        jaunes_dom=s.jaunes_a,
        jaunes_ext=s.jaunes_b,
        rouges_dom=s.rouges_a,
        rouges_ext=s.rouges_b,
        journal=match.journal,
    )

    resultats.append(r)
    appliquer_resultat(r, classement)


def simuler_saison(effectifs, seed=None):
    if seed is not None:
        random.seed(seed)

    classement = {nom: LigneClassement(nom=nom) for nom in effectifs}
    calendrier = generer_calendrier(list(effectifs))
    resultats = []

    for num_journee, journee in enumerate(calendrier, start=1):
        for dom, ext in journee:
            match = simuler_match(effectifs[dom], effectifs[ext], dom, ext)
            enregistrer_resultat(match, num_journee, classement, resultats)

    return classement, resultats


def trier_classement(classement):
    return sorted(
        classement.values(),
        key=lambda l: (l.points, l.difference, l.essais_marques),
        reverse=True,
    )


def afficher_classement(classement):
    lignes = trier_classement(classement)
    print("=" * 115)
    print(f"{'#':<3}{'Équipe':<28}{'J':>3}{'G':>4}{'N':>4}{'P':>4}{'BO':>4}{'BD':>4}{'Pts':>5}{'Diff':>6}{'E+':>4}{'E-':>4}{'Pén':>5}{'Dr':>4}{'J':>4}{'R':>4}")
    print("-" * 115)
    for i, l in enumerate(lignes, start=1):
        zone = ""
        if i <= 2:
            zone = "  ➤ Demi-finale directe"
        elif i <= 6:
            zone = "  ➤ Barrages"
        elif i == 13:
            zone = "  ➤ Barrage d'accession"
        elif i == 14:
            zone = "  ➤ Reléguation"
        print(
            f"{i:<3}{l.nom:<28}{l.joues:>3}{l.gagnes:>4}{l.nuls:>4}{l.perdus:>4}"
            f"{l.bonus_off:>4}{l.bonus_def:>4}{l.points:>5}{l.difference:>6}"
            f"{l.essais_marques:>4}{l.essais_encaisses:>4}{l.penalites:>5}{l.drops:>4}{l.jaunes:>4}{l.rouges:>4}{zone}"
        )
    print("=" * 115)


def afficher_stats_globales(resultats):
    n = len(resultats)
    total_essais = sum(r.essais_dom + r.essais_ext for r in resultats)
    total_penalites = sum(r.penalites_dom + r.penalites_ext for r in resultats)
    total_drops = sum(r.drops_dom + r.drops_ext for r in resultats)
    total_points = sum(r.score_dom + r.score_ext for r in resultats)
    total_jaunes = sum(r.jaunes_dom + r.jaunes_ext for r in resultats)
    total_rouges = sum(r.rouges_dom + r.rouges_ext for r in resultats)
    victoires_dom = sum(1 for r in resultats if r.score_dom > r.score_ext)
    nuls = sum(1 for r in resultats if r.score_dom == r.score_ext)
    ecarts = [abs(r.score_dom - r.score_ext) for r in resultats]
    gros_ecarts = sum(1 for e in ecarts if e > 15)

    print("\n=== STATISTIQUES GLOBALES DE LA SAISON ===")
    print(f"Matchs joués                 : {n}")
    print(f"Points marqués / match       : {total_points / n:.1f}  (Top 14 réel : ~45)")
    print(f"Essais / match               : {total_essais / n:.2f}  (Top 14 réel : ~4.5)")
    print(f"Pénalités / match            : {total_penalites / n:.2f}  (Top 14 réel : ~3.5)")
    print(f"Drops / match                : {total_drops / n:.2f}  (Top 14 réel : ~0.5)")
    print(f"Cartons jaunes / match       : {total_jaunes / n:.2f}  (Top 14 réel : ~2.0)")
    print(f"Cartons rouges / match       : {total_rouges / n:.2f}  (Top 14 réel : ~0.15)")
    print(f"Victoires à domicile         : {victoires_dom} ({100 * victoires_dom / n:.1f}% des matchs)  (Top 14 réel : ~60-65%)")
    print(f"Matchs nuls                  : {nuls} ({100 * nuls / n:.1f}%)")
    print(f"Écart moyen au score         : {sum(ecarts) / n:.1f} pts")
    print(f"Matchs à +15 pts d'écart      : {gros_ecarts} ({100 * gros_ecarts / n:.1f}%)")

def classement_apres_journee(effectifs, resultats, derniere_journee):
    """
    Reconstruit le classement tel qu'il était après la journée donnée,
    en ne prenant en compte que les matchs des journées 1 à derniere_journee.
    """
    classement = {nom: LigneClassement(nom=nom) for nom in effectifs}
    for r in resultats:
        if r.journee <= derniere_journee:
            appliquer_resultat(r, classement)
    return classement


def afficher_journee(classement, resultats, journee, effectifs=None):
    """
    Affiche les résultats de la journée demandée puis le classement mis à jour
    après cette journée.

    effectifs est optionnel : il sert à garantir que toutes les équipes
    apparaissent au classement, même si la journée est vide.
    """
    if effectifs is None:
        effectifs = {r.domicile: None for r in resultats}
        effectifs.update({r.exterieur: None for r in resultats})

    par_journee = {}
    for r in resultats:
        par_journee.setdefault(r.journee, []).append(r)

    matchs = par_journee.get(journee, [])
    print(f"┌─ JOURNÉE {journee} " + "─" * 90)
    for r in matchs:
        print(f"│  {r.domicile:<26} {r.score_dom:>2} - {r.score_ext:<2} {r.exterieur:<26}")
    print("└" + "─" * 98)

    classement_j = classement_apres_journee(effectifs, resultats, journee)
    print(f"╔═ CLASSEMENT APRÈS LA JOURNÉE {journee} " + "═" * 70)
    afficher_classement(classement_j)
    if journee<26:
        afficher_calendrier_vierge(effectifs, journees_a_afficher=[journee+1])


def afficher_calendrier(classement, resultats, journees_a_afficher=None):
    """
    Présentation ergonomique du calendrier : une ligne par journée, une par match,
    avec le numéro de journée, le score et le nom des équipes alignés.
    """
    par_journee = {}
    for r in resultats:
        par_journee.setdefault(r.journee, []).append(r)

    journees = sorted(par_journee) if journees_a_afficher is None else journees_a_afficher
    for num in journees:
        matchs = par_journee[num]
        print(f"┌─ JOURNÉE {num} " + "─" * 90)
        for r in matchs:
            dom = f"{r.domicile}"
            ext = f"{r.exterieur}"
            print(f"│  {dom:<26} {r.score_dom:>2} - {r.score_ext:<2} {ext:<26}")
        print("└" + "─" * 98)


def afficher_calendrier_vierge(effectifs, journees_a_afficher=None):
    """
    Affiche le calendrier avant simulation : numéro de journée et affiches,
    avec un marqueur (vs) pour distinguer domicile/extérieur.
    """
    calendrier = generer_calendrier(list(effectifs))
    journees = range(1, len(calendrier) + 1) if journees_a_afficher is None else journees_a_afficher
    for num in journees:
        matchs = calendrier[num - 1]
        print(f"┌─ JOURNÉE {num} " + "─" * 90)
        for dom, ext in matchs:
            print(f"│  {dom:<28} reçoit   {ext}")
        print("└" + "─" * 98)

def simuler_phases_finales(classement, effectifs, seed=None):
    """
    Phases finales au format Top 14 :
    - Barrages : 3e reçoit 6e, 4e reçoit 5e ;
    - Demi-finales (terrain neutre) : 1er vs le moins bien classé des vainqueurs
      de barrages, 2e vs l'autre vainqueur ;
    - Finale (terrain neutre) entre les deux vainqueurs de demi-finales.

    Retourne un dictionnaire : {
        "barrages": [match, match],
        "demi_finales": [match, match],
        "finale": match,
        "champion": str,
    }
    """
    if seed is not None:
        random.seed(seed)

    lignes = trier_classement(classement)
    t1, t2, t3, t4, t5, t6 = [l.nom for l in lignes[:6]]

    def jouer(dom, ext, tour, avantage_domicile=True, avantage_demi=False):
        match = simuler_match(effectifs[dom], effectifs[ext], dom, ext,
                              avantage_domicile=avantage_domicile, avantage_demi=avantage_demi)
        match.journal.insert(0, f"=== {tour} : {dom} vs {ext} ===")
        vainqueur = dom if match.score_a > match.score_b else ext
        return match, vainqueur

    barrage1, v_b1 = jouer(t3, t6, "BARRAGE")
    barrage2, v_b2 = jouer(t4, t5, "BARRAGE")

    # Demi-finales : le 1er affronte le vainqueur du barrage 4/5,
    # le 2e affronte le vainqueur du barrage 3/6 (bonus +3 pour les qualifiés directs)
    demi1, v_d1 = jouer(t1, v_b2, "DEMI-FINALE", avantage_domicile=False, avantage_demi=True)
    demi2, v_d2 = jouer(t2, v_b1, "DEMI-FINALE", avantage_domicile=False, avantage_demi=True)

    finale, champion = jouer(v_d1, v_d2, "FINALE", avantage_domicile=False, avantage_demi=False)

    return {
        "barrages": [barrage1, barrage2],
        "demi_finales": [demi1, demi2],
        "finale": finale,
        "champion": champion,
    }


def afficher_phases_finales(phases):
    print("\n=== PHASES FINALES ===")
    for barrage in phases["barrages"]:
        afficher_resultat_phases(barrage, "Barrage")
    for demi in phases["demi_finales"]:
        afficher_resultat_phases(demi, "Demi-finale")
    afficher_resultat_phases(phases["finale"], "FINALE")
    print(f"\n🏆 CHAMPION DE FRANCE : {phases['champion']} !")


def afficher_resultat_phases(match, tour):
    print(f"  {tour:<12} {match.nom_a} {match.score_a} - {match.score_b} {match.nom_b}")
    
    
    
def afficher_alternation(effectifs):
    """
    Contrôle de réalisme : longueur de la plus longue série consécutive
    sur le même terrain, par équipe (objectif : 2 max).
    """
    calendrier = generer_calendrier(list(effectifs))
    stats = stats_alternation(calendrier, list(effectifs))
    print("Plus longue série consécutive sur le même terrain (objectif <= 2) :")
    for nom, v in sorted(stats.items(), key=lambda kv: -kv[1]):
        marque = "✅" if v <= 2 else "❌"
        print(f"  {marque} {nom:<28}{v} match(s)")
        

        

if __name__ == "__main__":
    classement, resultats = simuler_saison(EFFECTIFS_TOP14, seed=2026)
    print(f"Saison simulée : {max(r.journee for r in resultats)} journées, {len(resultats)} matchs.\n")
    afficher_classement(classement)
    afficher_stats_globales(resultats)
    phases = simuler_phases_finales(classement, EFFECTIFS_TOP14, seed=2027)
    afficher_phases_finales(phases)