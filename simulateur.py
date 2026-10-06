"""Simulateur de match de rugby à XV."""

import random
import time
from dataclasses import dataclass, field

POINTS = {"essai": 5, "transformation": 2, "penalite": 3, "drop": 3}


@dataclass
class Equipe:
    nom: str
    attaque: int  # 1-100
    defense: int  # 1-100
    physique: int  # 1-100 (mêlées, touches, rucks)
    discipline: int  # 1-100 (faiblesse de pénalités concédées)
    score: int = 0
    stats: dict = field(default_factory=lambda: {
        "essais": 0, "transformations": 0, "penalites": 0, "drops": 0,
        "fautes": 0,
    })

    @property
    def force(self):
        return round((self.attaque + self.defense + self.physique + self.discipline) / 4)


def charger_equipe(nom: str) -> Equipe:
    """Crée une équipe avec des stats aléatoires équilibrées (60-90)."""
    return Equipe(
        nom=nom,
        attaque=random.randint(60, 90),
        defense=random.randint(60, 90),
        physique=random.randint(60, 90),
        discipline=random.randint(60, 90),
    )


class Match:
    def __init__(self, domicile: Equipe, exterieur: Equipe, minute_max: int = 80, verbose: bool = True):
        self.domicile = domicile
        self.exterieur = exterieur
        self.minute_max = minute_max
        self.verbose = verbose
        self.minute = 0
        self.possession = random.choice([domicile, exterieur])

    def log(self, message: str):
        if self.verbose:
            print(message)

    def avantage(self, attaquant: Equipe, defenseur: Equipe) -> float:
        """Probabilité que l'attaquant garde/marque sur une phase."""
        base = 0.5
        ecart = (attaquant.force - defenseur.force) / 100
        return max(0.1, min(0.9, base + ecart * 0.5))

    def phase(self, porteur: Equipe, adversaire: Equipe):
        """Simule une phase de jeu d'environ 2 minutes."""
        actions = [
            "grosse percussion au milieu du terrain",
            "série de passes rapides",
            "coup de pied par-dessus la défense",
            "pick-and-go près des poteaux",
            "maul puissant après une touche",
            "chute dans le ruck adverse",
            "combination en ligne des trois-quarts",
        ]
        self.log(f"[{self.minute:>2}'] {porteur.nom} : {random.choice(actions)}...")

        p = self.avantage(porteur, adversaire)

        roll = random.random()
        if roll < p * 0.30:
            # Essai !
            self.log(f"      🏉 ESSAI de {porteur.nom} !")
            porteur.score += POINTS["essai"]
            porteur.stats["essais"] += 1
            # Transformation
            if random.random() < 0.35 + porteur.force / 250:
                porteur.score += POINTS["transformation"]
                porteur.stats["transformations"] += 1
                self.log(f"      ✅ Transformation réussie ! ({porteur.score}-{adversaire.score})")
            else:
                self.log(f"      ❌ Transformation manquée ({porteur.score}-{adversaire.score})")
            self.possession = adversaire
        elif roll < p * 0.55:
            # Pénalité
            self.log(f"      📍 Pénalité obtenue par {porteur.nom} !")
            if random.random() < 0.35 + porteur.force / 200:
                # Tentative de tir
                if random.random() < 0.75:
                    porteur.score += POINTS["penalite"]
                    porteur.stats["penalites"] += 1
                    self.log(f"      ✅ Pénalité passée par {porteur.nom} ! ({porteur.score}-{adversaire.score})")
                else:
                    self.log(f"      ❌ Pénalité manquée ({porteur.score}-{adversaire.score})")
            # Relance ou occupation
        elif roll < p * 0.70:
            # Drop
            if random.random() < 0.15:
                if random.random() < 0.6:
                    porteur.score += POINTS["drop"]
                    porteur.stats["drops"] += 1
                    self.log(f"      ✅ Drop réussi par {porteur.nom} ! ({porteur.score}-{adversaire.score})")
                else:
                    self.log("      ❌ Drop manqué, occupation maintenue")
        elif roll < p * 0.90:
            # Occupation / jeu au pied
            self.log(f"      👟 Dégagement de {porteur.nom}, {adversaire.nom} relance")
            self.possession = adversaire
        else:
            # Faute / perte de balle
            if random.random() < 0.5:
                adversaire.stats["fautes"] += 1
                self.log(f"      ⚠️  Faute de {porteur.nom}, pénalité pour {adversaire.nom}")
            else:
                self.log(f"      🔄 Ballon perdu, {adversaire.nom} récupère")
            self.possession = adversaire

    def simuler(self):
        self.log("=" * 60)
        self.log(f"  {self.domicile.nom}  vs  {self.exterieur.nom}")
        self.log(f"  Forces : {self.domicile.force} / {self.exterieur.force}")
        self.log("=" * 60)

        while self.minute < self.minute_max:
            self.minute += 2
            self.phase(self.possession, self.domicile if self.possession == self.exterieur else self.exterieur)

        self.log("=" * 60)
        self.log("  COUP DE SIFFLET FINAL")
        self.log(f"  {self.domicile.nom} {self.domicile.score} - {self.exterieur.score} {self.exterieur.nom}")
        self.log("=" * 60)

        if self.domicile.score > self.exterieur.score:
            self.log(f"  🏆 Victoire de {self.domicile.nom} !")
            return self.domicile
        if self.exterieur.score > self.domicile.score:
            self.log(f"  🏆 Victoire de {self.exterieur.nom} !")
            return self.exterieur
        self.log("  🤝 Match nul !")
        return None


def main():
    random.seed()  # Nouveau match à chaque exécution
    print("🏉 SIMULATEUR DE MATCH DE RUGBY 🏉\n")
    dom = charger_equipe(input("Nom de l'équipe domicile : ").strip() or "Domicile")
    ext = charger_equipe(input("Nom de l'équipe extérieure : ").strip() or "Extérieur")
    print()
    match = Match(dom, ext)
    match.simuler()


if __name__ == "__main__":
    main()
