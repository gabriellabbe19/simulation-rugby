# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 00:26:03 2026

@author: gabri
"""

import statistics
from collections import Counter

from Saison import (
    EFFECTIFS_TOP14,
    afficher_stats_globales,
    simuler_saison,
    trier_classement,
    simuler_phases_finales
)


NB_SAISONS = 100
SEED_DEPART = 2026


def analyser():
    titres = Counter()              # champions après phases finales
    finalistes = Counter()          # équipes ayant atteint la finale
    leaders_reguliere = Counter()   # 1ers de la saison régulière
    leader_champion = 0             # saisons où le 1er a confirmé en playoffs
    top2 = Counter()
    top6 = Counter()
    relagues = Counter()
    points_premier = []
    points_dernier = []
    points_2 = []
    points_6 = []
    points_12 = []
    ecarts_champion = []

    somme = {
        "points_match": 0.0,
        "essais_match": 0.0,
        "penalites_match": 0.0,
        "drops_match": 0.0,
        "jaunes_match": 0.0,
        "rouges_match": 0.0,
        "victoires_dom": 0,
        "nuls": 0,
        "matchs": 0,
        "ecart" : 0,
        "gros_ecart": 0,
    }

    for seed in range(SEED_DEPART, SEED_DEPART + NB_SAISONS):
        classement, resultats = simuler_saison(EFFECTIFS_TOP14, seed=seed)
        lignes = trier_classement(classement)

        leaders_reguliere[lignes[0].nom] += 1

        # Phases finales : sans nouveau seed, elles continuent le flux
        # aléatoire de la saison -> reproductibles pour un seed donné.
        phases = simuler_phases_finales(classement, EFFECTIFS_TOP14)
        champion = phases["champion"]
        titres[champion] += 1
        finalistes[phases["finale"].nom_a] += 1
        finalistes[phases["finale"].nom_b] += 1
        if champion == lignes[0].nom:
            leader_champion += 1

        for l in lignes[:2]:
            top2[l.nom] += 1
        for l in lignes[:6]:
            top6[l.nom] += 1
        for l in lignes[-1:]:
            relagues[l.nom] += 1

        points_premier.append(lignes[0].points)
        points_dernier.append(lignes[-1].points)
        points_2.append(lignes[1].points)
        points_6.append(lignes[5].points)
        points_12.append(lignes[11].points)
        ecarts_champion.append(classement[champion].difference)

        for r in resultats:
            somme["matchs"] += 1
            somme["points_match"] += r.score_dom + r.score_ext
            somme["essais_match"] += r.essais_dom + r.essais_ext
            somme["penalites_match"] += r.penalites_dom + r.penalites_ext
            somme["drops_match"] += r.drops_dom + r.drops_ext
            somme["jaunes_match"] += r.jaunes_dom + r.jaunes_ext
            somme["rouges_match"] += r.rouges_dom + r.rouges_ext
            somme["ecart"] += abs(r.score_dom - r.score_ext)
            somme["gros_ecart"] += 1 if abs(r.score_dom - r.score_ext) > 15 else 0
            if r.score_dom > r.score_ext:
                somme["victoires_dom"] += 1
            elif r.score_dom == r.score_ext:
                somme["nuls"] += 1

    return (titres, finalistes, leaders_reguliere, leader_champion, top2, top6,
            relagues, points_premier, points_dernier, points_2, points_6,
            points_12, ecarts_champion, somme)

def afficher_analyse():
    (titres, finalistes, leaders_reguliere, leader_champion, top2, top6,
            relagues, points_premier, points_dernier, points_2, points_6,
            points_12, ecarts_champion, somme) = analyser()

    noms = list(EFFECTIFS_TOP14)

    print(f"=== ANALYSE DE {NB_SAISONS} SAISONS (graines {SEED_DEPART} à {SEED_DEPART + NB_SAISONS - 1}) ===\n")

    print("--- Qui gagne le titre ? ---")
    for nom, nb in titres.most_common():
        print(f"  {nom:<28}{nb:>3} titre(s)  ({100 * nb / NB_SAISONS:.0f}%)")
    print()

    print("--- Taux de présence par zone (en % des saisons) ---")
    print(f"{'Équipe':<28}{'Titre':>7}{'Top 2':>8}{'Top 6':>8}{'Relég.':>8}")
    for nom in sorted(noms, key=lambda x: -titres[x]):
        print(
            f"{nom:<28}"
            f"{100 * titres[nom] / NB_SAISONS:>6.0f}%"
            f"{100 * top2[nom] / NB_SAISONS:>7.0f}%"
            f"{100 * top6[nom] / NB_SAISONS:>7.0f}%"
            f"{100 * relagues[nom] / NB_SAISONS:>7.0f}%"
        )
    print()

    print("--- Serrage du classement ---")
    print(f"Points du champion       : {statistics.mean(points_premier):.1f} de moyenne (min {min(points_premier)}, max {max(points_premier)})")
    print(f"Points du dernier        : {statistics.mean(points_dernier):.1f} de moyenne (min {min(points_dernier)}, max {max(points_dernier)})")
    print(f"Points 2e           : {statistics.mean(points_2):.1f} pts en moyenne")
    print(f"Points 6e (barrage)  : {statistics.mean(points_6):.1f} pts en moyenne")
    print(f"Points 12e (maint.) : {statistics.mean(points_12):.1f} pts en moyenne")
    print(f"Diff. de points du champion : {statistics.mean(ecarts_champion):.0f} en moyenne")
    print()

    n = somme["matchs"]
    print("--- Style de jeu moyen (toutes saisons confondues) vs Top 14 réel ---")
    print(f"Points / match       : {somme['points_match'] / n:.1f}   (réel : ~55)")
    print(f"Essais / match       : {somme['essais_match'] / n:.2f}   (réel : ~6/7)")
    print(f"Pénalités / match    : {somme['penalites_match'] / n:.2f}   (réel : ~3)")
    print(f"Drops / match        : {somme['drops_match'] / n:.2f}   (réel : ~0.05)")
    print(f"Cartons jaunes / m.  : {somme['jaunes_match'] / n:.2f}   (réel : ~2.0)")
    print(f"Cartons rouges / m.  : {somme['rouges_match'] / n:.2f}   (réel : ~0.1)")
    print(f"Victoires à domicile : {100 * somme['victoires_dom'] / n:.1f}%  (réel : ~65-70%)")
    print(f"Matchs nuls          : {100 * somme['nuls'] / n:.1f}%   (réel : ~2-3%)")
    print(f"Ecart moyen au score : {somme['ecart'] / n:.1f}   (réel : ~18 points)")
    print(f"Ecart de plus de 15 points : {100 * somme['gros_ecart'] / n:.1f}%   (réel : ~50%)")

    nb_champions_diff = len(titres)
    part_max = titres.most_common(1)[0][1] / NB_SAISONS
    print("\n--- Équilibre compétitif ---")
    print(f"Nombre de champions différents en {NB_SAISONS} saisons : {nb_champions_diff} / 14")
    print(f"Meilleur club : {titres.most_common(1)[0][0]} avec {100 * part_max:.0f}% des titres")
    if part_max > 0.5:
        print("⚠️  Un club rafle plus de la moitié des titres : domination excessive.")
    elif nb_champions_diff >= 6 and part_max <= 0.35:
        print("✅  Diffusion des titres comparable à un championnat réel (6-9 champions différents).")
    else:
        print("ℹ️  Domination notable mais plausible ; comparer à l'histoire récente du Top 14.")


if __name__ == "__main__":
    afficher_analyse()