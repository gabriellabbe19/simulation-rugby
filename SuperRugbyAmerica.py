# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 17:51:30 2026

@author: gabri
"""
import random
from collections import Counter
from itertools import combinations

from moteur import simuler_match
from Saison import (
    LigneClassement,
    classement_apres_journee,
    enregistrer_resultat,
    stats_alternation,
    trier_classement,
)


NB_JOURNEES = 18

CONFERENCES = {
    "Conférence Sud": {
        "Division Argentine": ["Dogos XV", "Pampas XV", "Tarucas", "Capibaras XV"],
        "Division Sudamericanas": ["Peñarol", "Yacaré", "Cobras", "Selknam"],
    },
    "Conférence Nord": {
        "Division West": ["Utah Warriors", "Colorado Raptors", "California Legion", "Seattle Seawolves"],
        "Division East": ["Old Glory DC", "Chicago Hounds", "New England Free Jacks", "Piranhas de Montréal"],
    },
}

CODE_DIVISION = {
    "Division Argentine": "ARG",
    "Division Sudamericanas": "SUD",
    "Division West": "WST",
    "Division East": "EST",
}

EFFECTIFS_AMERICAS = {
    "Dogos XV":                {"World Class": 0, "International": 0, "National": 8, "Pro": 28, "Semi-Pro": 4, "Amateur": 0},
    "Pampas XV":               {"World Class": 0, "International": 0, "National": 6, "Pro": 33, "Semi-Pro": 1, "Amateur": 0},
    "Tarucas":                 {"International": 0, "National": 4, "Pro": 34, "Semi-Pro": 2, "Amateur": 0},
    "Capibaras XV":            {"International": 0, "National": 5, "Pro": 33, "Semi-Pro": 2, "Amateur": 0},
    "Peñarol":                 {"International": 0, "National": 8, "Pro": 25, "Semi-Pro": 7, "Amateur": 0},
    "Yacaré":                  {"International": 0, "National": 2, "Pro": 31, "Semi-Pro": 7, "Amateur": 0},
    "Cobras":                  {"National": 1, "Pro": 29, "Semi-Pro": 10, "Amateur": 0},
    "Selknam":                 {"International": 0, "National": 8, "Pro": 22, "Semi-Pro": 10, "Amateur": 0},
    "Utah Warriors":           {"International": 0, "National": 1, "Pro": 29, "Semi-Pro": 10, "Amateur": 0},
    "Colorado Raptors":        {"National": 1, "Pro": 31, "Semi-Pro": 8, "Amateur": 0},
    "California Legion":       {"International": 0, "National": 4, "Pro": 30, "Semi-Pro": 10, "Amateur": 0},
    "Seattle Seawolves":       {"International": 0, "National": 4, "Pro": 21, "Semi-Pro": 15, "Amateur": 0},
    "Old Glory DC":            {"International": 0, "National": 5, "Pro": 28, "Semi-Pro": 7, "Amateur": 0},
    "Chicago Hounds":          {"International": 0, "National": 9, "Pro": 24, "Semi-Pro": 7, "Amateur": 0},
    "New England Free Jacks":  {"World Class": 0, "International": 0, "National": 3, "Pro": 34, "Semi-Pro": 5, "Amateur": 0},
    "Piranhas de Montréal":    {"International": 1, "National": 10, "Pro": 13, "Semi-Pro": 15, "Amateur": 2},
}


def _divisions():
    return [(nom, equipes) for conf in CONFERENCES.values() for nom, equipes in conf.items()]


def _division_de(equipe):
    for nom, equipes in _divisions():
        if equipe in equipes:
            return nom
    return None


def generer_matchs():
    """
    Liste des 144 matchs de la saison (doubles aller-retour en division,
    match unique contre chaque équipe des autres divisions, 2 réceptions
    et 2 déplacements par division adverse).
    """
    divisions = [equipes for _, equipes in _divisions()]
    matchs = []
    for equipes in divisions:
        for i, a in enumerate(equipes):
            for b in equipes[i + 1:]:
                matchs.append((a, b))
                matchs.append((b, a))
    for X, Y in combinations(divisions, 2):
        for i, x in enumerate(X):
            for j, y in enumerate(Y):
                if (i + j) % 2 == 0:
                    matchs.append((y, x))
                else:
                    matchs.append((x, y))
    return matchs


def construire_journees():
    """
    Construction directe des 18 journées (une équipe = un match par journée) :

    - 6 journées de derbys : chaque division joue ses 3 matchings parfaits
      de K4, chacun en deux sens (aller puis retour), soit 12 matchs internes
      par division et 3 réceptions / 3 déplacements ;

    - 12 journées inter-divisions : les 6 paires de divisions sont regroupées
      en 3 arrangements disjoints ((A,B)+(C,D), (A,C)+(B,D), (A,D)+(B,C)),
      chacun développé en 4 journées par décalage cyclique : x_i rencontre
      y_(i+k) mod 4. Chaque paire de divisions se rencontre ainsi 4 fois par
      équipe, avec 2 réceptions et 2 déplacements par parité des positions.
    """
    divisions = [equipes for _, equipes in _divisions()]
    journees = []

    factorisations = [
        [(0, 1), (2, 3)],
        [(0, 2), (1, 3)],
        [(0, 3), (1, 2)],
    ]
    for f in factorisations:
        for doublon in range(2):
            journee = []
            for equipes in divisions:
                for a, b in f:
                    x, y = equipes[a], equipes[b]
                    journee.append((x, y) if doublon == 0 else (y, x))
            journees.append(journee)

    arrangements = [
        [(0, 1), (2, 3)],
        [(0, 2), (1, 3)],
        [(0, 3), (1, 2)],
    ]
    for paire_a, paire_b in arrangements:
        for k in range(4):
            journee = []
            for dx, dy in (paire_a, paire_b):
                x_list, y_list = divisions[dx], divisions[dy]
                for i in range(4):
                    j = (i + k) % 4
                    if (i + j) % 2 == 0:
                        journee.append((y_list[j], x_list[i]))
                    else:
                        journee.append((x_list[i], y_list[j]))
            journees.append(journee)

    return journees


def _venues_par_journee(journees):
    venues = []
    for journee in journees:
        v = {}
        for dom, ext in journee:
            v[dom] = "D"
            v[ext] = "E"
        venues.append(v)
    return venues


def _cout_alternation(venues, equipes):
    total = 0
    for e in equipes:
        prec1 = prec2 = None
        for v in venues:
            s = v[e]
            if prec2 == s and prec1 == s:
                total += 1
            prec2 = prec1
            prec1 = s
    return total


def _descente_alternation(journees, venues, equipes):
    cout = _cout_alternation(venues, equipes)
    n = len(journees)
    ameliore = True
    while ameliore and cout > 0:
        ameliore = False
        for i in range(n):
            for j in range(i + 1, n):
                journees[i], journees[j] = journees[j], journees[i]
                venues[i], venues[j] = venues[j], venues[i]
                nouveau = _cout_alternation(venues, equipes)
                if nouveau < cout:
                    cout = nouveau
                    ameliore = True
                    break
                journees[i], journees[j] = journees[j], journees[i]
                venues[i], venues[j] = venues[j], venues[i]
            if ameliore:
                break
    return cout


def optimiser_alternation(journees, equipes, relances=25):
    """
    Réordonne les journées (sans toucher à leur contenu) pour éliminer
    les séries de 3+ matchs consécutifs à domicile ou à l'extérieur.
    Descente locale par échanges de journées, avec relances aléatoires.
    Retourne (calendrier, cout résiduel ; 0 = parfait).
    """
    venues = _venues_par_journee(journees)
    meilleur_j = list(journees)
    meilleur_v = list(venues)
    meilleur_cout = _descente_alternation(meilleur_j, meilleur_v, equipes)
    for _ in range(relances):
        if meilleur_cout == 0:
            break
        ordre = list(range(len(journees)))
        random.shuffle(ordre)
        j_essai = [journees[k] for k in ordre]
        v_essai = [venues[k] for k in ordre]
        cout = _descente_alternation(j_essai, v_essai, equipes)
        if cout < meilleur_cout:
            meilleur_j, meilleur_v, meilleur_cout = j_essai, v_essai, cout
    return meilleur_j, meilleur_cout


def generer_calendrier_americain(effectifs, verifie=True, optimise=True):
    journees = construire_journees()
    if optimise:
        equipes = list(effectifs)
        journees, cout = optimiser_alternation(journees, equipes)
        if cout > 0:
            print(f"⚠️  {cout} série(s) de 3+ terrains identiques n'ont pas pu être éliminées.")
    if verifie:
        erreurs = verifier_calendrier(journees, effectifs)
        if erreurs:
            raise RuntimeError("Calendrier invalide : " + " ; ".join(erreurs))
    return journees


def _bilan_deplacements(matchs):
    """
    Pour chaque équipe, contre chaque division : la liste des équipes
    reçues et celle des équipes chez qui elle se déplace.
    """
    bilan = {}
    for dom, ext in matchs:
        div_ext = _division_de(ext)
        div_dom = _division_de(dom)
        bilan.setdefault(dom, {}).setdefault(div_ext, {"recoit": [], "deplace": []})["recoit"].append(ext)
        bilan.setdefault(ext, {}).setdefault(div_dom, {"recoit": [], "deplace": []})["deplace"].append(dom)
    return bilan


def verifier_calendrier(journees, effectifs):
    """Contrôle toutes les contraintes du format ; retourne la liste des défauts."""
    erreurs = []
    equipes = list(effectifs)
    matchs = [m for journee in journees for m in journee]

    if len(journees) != NB_JOURNEES:
        erreurs.append(f"{len(journees)} journées au lieu de {NB_JOURNEES}")
    if len(matchs) != 144:
        erreurs.append(f"{len(matchs)} matchs au lieu de 144")

    for num, journee in enumerate(journees, start=1):
        if len(journee) != len(equipes) // 2:
            erreurs.append(f"Journée {num} : {len(journee)} matchs")
        presents = [t for m in journee for t in m]
        if len(set(presents)) != len(presents):
            erreurs.append(f"Journée {num} : une équipe joue deux fois")

    bilan = _bilan_deplacements(matchs)
    for equipe in equipes:
        for division, volets in bilan.get(equipe, {}).items():
            recoit = volets["recoit"]
            deplace = volets["deplace"]
            if division == _division_de(equipe):
                if sorted(recoit) != sorted(deplace) or len(recoit) != 3:
                    erreurs.append(f"{equipe} : aller-retour incomplet en division")
            else:
                if len(recoit) != 2 or len(deplace) != 2:
                    erreurs.append(
                        f"{equipe} vs {division} : {len(recoit)} réceptions, {len(deplace)} déplacements (attendu 2/2)"
                    )
        total_recoit = sum(len(v["recoit"]) for v in bilan.get(equipe, {}).values())
        total_deplace = sum(len(v["deplace"]) for v in bilan.get(equipe, {}).values())
        if total_recoit != 9 or total_deplace != 9:
            erreurs.append(f"{equipe} : {total_recoit} réceptions / {total_deplace} déplacements (attendu 9/9)")
    return erreurs


def simuler_saison_americaine(effectifs, seed=None):
    if seed is not None:
        random.seed(seed)

    journees = generer_calendrier_americain(effectifs)
    classement = {nom: LigneClassement(nom=nom) for nom in effectifs}
    resultats = []

    for num_journee, journee in enumerate(journees, start=1):
        for dom, ext in journee:
            match = simuler_match(effectifs[dom], effectifs[ext], dom, ext)
            enregistrer_resultat(match, num_journee, classement, resultats)

    return classement, resultats


def afficher_classement_americain(classement):
    lignes = trier_classement(classement)
    print("=" * 110)
    print(f"{'#':<3}{'Équipe':<25}{'Div':<5}{'J':>3}{'G':>4}{'N':>4}{'P':>4}{'BO':>4}{'BD':>4}{'Pts':>5}{'Diff':>6}{'E+':>4}{'E-':>4}{'Pén':>5}{'Dr':>4}{'J':>4}{'R':>4}")
    print("-" * 110)
    for i, l in enumerate(lignes, start=1):
        print(
            f"{i:<3}{l.nom:<25}{CODE_DIVISION[_division_de(l.nom)]:<5}{l.joues:>3}{l.gagnes:>4}{l.nuls:>4}{l.perdus:>4}"
            f"{l.bonus_off:>4}{l.bonus_def:>4}{l.points:>5}{l.difference:>6}"
            f"{l.essais_marques:>4}{l.essais_encaisses:>4}{l.penalites:>5}{l.drops:>4}{l.jaunes:>4}{l.rouges:>4}"
        )
    print("=" * 110)


def afficher_journee_americaine(resultats, journee, effectifs):
    par_journee = {}
    for r in resultats:
        par_journee.setdefault(r.journee, []).append(r)

    matchs = par_journee.get(journee, [])
    print(f"┌─ JOURNÉE {journee} " + "─" * 85)
    for r in matchs:
        print(f"│  {r.domicile:<24} {r.score_dom:>2} - {r.score_ext:<2} {r.exterieur:<24}")
    print("└" + "─" * 93)

    classement_j = classement_apres_journee(effectifs, resultats, journee)
    print(f"╔═ CLASSEMENT APRÈS LA JOURNÉE {journee} " + "═" * 65)
    afficher_classement_americain(classement_j)


def _conference_de(equipe):
    for conf in CONFERENCES:
        for division, equipes in CONFERENCES[conf].items():
            if equipe in equipes:
                return conf
    return None


def classement_conference(classement, conf):
    """Classement général filtré sur une conférence."""
    equipes_conf = {e for d in CONFERENCES[conf].values() for e in d}
    return [l for l in trier_classement(classement) if l.nom in equipes_conf]


def afficher_classements_conferences(classement):
    """
    Affiche le classement de chaque conférence avec la zone de qualification
    en demi-finales (top 4).
    """
    for conf in CONFERENCES:
        lignes = classement_conference(classement, conf)
        print(f"\n=== {conf.upper()} ===")
        print("=" * 95)
        print(f"{'#':<3}{'Équipe':<25}{'Div':<5}{'J':>3}{'G':>4}{'N':>4}{'P':>4}{'BO':>4}{'BD':>4}{'Pts':>5}{'Diff':>6}")
        print("-" * 95)
        for i, l in enumerate(lignes, start=1):
            zone = "  ➤ Demi-finale de conférence" if i <= 4 else ""
            print(
                f"{i:<3}{l.nom:<25}{CODE_DIVISION[_division_de(l.nom)]:<5}{l.joues:>3}{l.gagnes:>4}{l.nuls:>4}{l.perdus:>4}"
                f"{l.bonus_off:>4}{l.bonus_def:>4}{l.points:>5}{l.difference:>6}{zone}"
            )
        print("=" * 95)


def simuler_playoffs(classement, effectifs, seed=None):
    """
    Phases finales :
    - demi-finales de conférence : 1er vs 4e, 2e vs 3e (terrain du mieux classé) ;
    - finale de conférence : terrain du finaliste le mieux classé en saison régulière ;
    - GRANDE FINALE : vainqueur Sud vs vainqueur Nord, terrain neutre.

    En cas de match nul, l'équipe la mieux classée l'emporte (prolongation).

    Retourne : {
        "Conférence Sud": {"demi_finales": [...], "finale": match, "vainqueur": str},
        "Conférence Nord": {...},
        "finale_americaine": match,
        "champion": str,
    }
    """
    if seed is not None:
        random.seed(seed)

    lignes_conf = {conf: classement_conference(classement, conf) for conf in CONFERENCES}
    rang_conf = {
        conf: {l.nom: i for i, l in enumerate(lignes_conf[conf], start=1)}
        for conf in CONFERENCES
    }
    rang_global = {l.nom: i for i, l in enumerate(trier_classement(classement), start=1)}

    def jouer(dom, ext, tour, avantage_domicile=True, favori=None):
        if favori is None:
            favori = dom
        match = simuler_match(effectifs[dom], effectifs[ext], dom, ext,
                              avantage_domicile=avantage_domicile)
        match.journal.insert(0, f"=== {tour} : {dom} vs {ext} ===")
        if match.score_a > match.score_b:
            vainqueur = dom
        elif match.score_a < match.score_b:
            vainqueur = ext
        else:
            vainqueur = favori
            match.journal.append(f"Match nul à la fin du temps réglementaire : {favori} l'emporte en prolongation !")
        return match, vainqueur

    playoffs = {}
    for conf in CONFERENCES:
        lignes = lignes_conf[conf]
        e1, e2, e3, e4 = [l.nom for l in lignes[:4]]

        demi1, v1 = jouer(e1, e4, f"DEMI-FINALE {conf}", favori=e1)
        demi2, v2 = jouer(e2, e3, f"DEMI-FINALE {conf}", favori=e2)

        hote = v1 if rang_conf[conf][v1] <= rang_conf[conf][v2] else v2
        autre = v2 if hote == v1 else v1
        finale_conf, vainqueur_conf = jouer(
            hote, autre, f"FINALE {conf}", favori=hote
        )

        playoffs[conf] = {
            "demi_finales": [(demi1, e1, e4), (demi2, e2, e3)],
            "finale": (finale_conf, hote, autre),
            "vainqueur": vainqueur_conf,
        }

    vainq_sud = playoffs["Conférence Sud"]["vainqueur"]
    vainq_nord = playoffs["Conférence Nord"]["vainqueur"]

    favori_finale = vainq_sud if rang_global[vainq_sud] < rang_global[vainq_nord] else vainq_nord
    finale_am, champion = jouer(
        vainq_sud, vainq_nord, "GRANDE FINALE AMERICAS",
        avantage_domicile=False, favori=favori_finale
    )

    playoffs["finale_americaine"] = (finale_am, vainq_sud, vainq_nord)
    playoffs["champion"] = champion
    return playoffs


def afficher_playoffs(playoffs):
    print("\n=== PHASES FINALES ===")
    for conf in CONFERENCES:
        print(f"\n--- {conf} ---")
        for match, dom, ext in playoffs[conf]["demi_finales"]:
            print(f"  Demi-finale   {dom:<24} {match.score_a:>2} - {match.score_b:<2} {ext:<24}")
        match, dom, ext = playoffs[conf]["finale"]
        print(f"  Finale        {dom:<24} {match.score_a:>2} - {match.score_b:<2} {ext:<24}")
        print(f"  ➤ Vainqueur de la conférence : {playoffs[conf]['vainqueur']}")

    match, sud, nord = playoffs["finale_americaine"]
    print(f"\n--- GRANDE FINALE SR AMERICAS (terrain neutre) ---")
    print(f"  {sud} (Sud) {match.score_a} - {match.score_b} {nord} (Nord)")
    print(f"\n🏆 CHAMPION DES AMERICAS : {playoffs['champion']} !")


def afficher_stats_americaines(resultats):
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

    print("\n=== STATISTIQUES GLOBALES DE LA SAISON ===")
    print(f"Matchs joués                 : {n}")
    print(f"Points marqués / match       : {total_points / n:.1f}")
    print(f"Essais / match               : {total_essais / n:.2f}")
    print(f"Pénalités / match            : {total_penalites / n:.2f}")
    print(f"Drops / match                : {total_drops / n:.2f}")
    print(f"Cartons jaunes / match       : {total_jaunes / n:.2f}")
    print(f"Cartons rouges / match       : {total_rouges / n:.2f}")
    print(f"Victoires à domicile         : {victoires_dom} ({100 * victoires_dom / n:.1f}% des matchs)")
    print(f"Matchs nuls                  : {nuls} ({100 * nuls / n:.1f}%)")
    print(f"Écart moyen au score         : {sum(ecarts) / n:.1f} pts")


def afficher_controles(effectifs):
    """
    Contrôles de réalisme du calendrier : contraintes de format,
    alternance des terrains et déplacements par division.
    """
    journees = generer_calendrier_americain(effectifs)
    equipes = list(effectifs)
    matchs = [m for journee in journees for m in journee]

    erreurs = verifier_calendrier(journees, effectifs)
    print("=== CONTRÔLES DU CALENDRIER ===")
    if erreurs:
        for e in erreurs:
            print(f"  ❌ {e}")
    else:
        print(f"  ✅ {NB_JOURNEES} journées, 8 matchs chacune, 9 réceptions / 9 déplacements par équipe")
        print("  ✅ 2 réceptions et 2 déplacements contre chacune des divisions adverses")

    stats = stats_alternation(journees, equipes)
    if all(v <= 2 for v in stats.values()):
        print("  ✅ Aucune équipe n'enchaîne 3 matchs consécutifs sur le même terrain")
    else:
        for nom, v in sorted(stats.items(), key=lambda kv: -kv[1]):
            if v > 2:
                print(f"  ❌ {nom} : {v} matchs consécutifs sur le même terrain")

    bilan = _bilan_deplacements(matchs)
    print("\n  Déplacements par division (équipes reçues / équipes visitées) :")
    for equipe in equipes:
        lignes = []
        for division in [d for d in CONFERENCES for d in CONFERENCES[d]]:
            if division == _division_de(equipe):
                continue
            volets = bilan[equipe][division]
            lignes.append(f"{CODE_DIVISION[division]} : reçoit {', '.join(volets['recoit'])} | va à {', '.join(volets['deplace'])}")
        print(f"  {equipe:<25}")
        for ligne in lignes:
            print(f"      {ligne}")


if __name__ == "__main__":
    classement, resultats = simuler_saison_americaine(EFFECTIFS_AMERICAS, seed=2027)
    print(f"Saison simulée : {NB_JOURNEES} journées, {len(resultats)} matchs.\n")
    afficher_classement_americain(classement)
    afficher_classements_conferences(classement)
    afficher_stats_americaines(resultats)
    playoffs = simuler_playoffs(classement, EFFECTIFS_AMERICAS)
    afficher_playoffs(playoffs)
    