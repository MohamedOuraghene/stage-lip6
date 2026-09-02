"""Justification du seuil Δt : distribution des durées de transit.

À lancer depuis la racine du projet : python -m src.exploration_transit
"""

import matplotlib.pyplot as plt
import pandas as pd

from src.config import DATA_CLEAN_DIR, DELTA_T_DAYS, FIGURES_DIR

# Bornes de la zone creuse séparant les trajets réels des artefacts de censure
CREUX = (20, 55)


def durees_transit(year):
    """Jours écoulés entre le départ d'une escale et l'arrivée à la suivante."""
    chemin = DATA_CLEAN_DIR / f"stays_basic_info_{year}_clean.parquet"
    df = pd.read_parquet(chemin)
    df["ARRIVAL DATE"] = pd.to_datetime(df["ARRIVAL DATE"])
    df["SAILING DATE"] = pd.to_datetime(df["SAILING DATE"])

    df = df.sort_values(["VESSEL ID", "ARRIVAL DATE"])
    prochaine_arrivee = df.groupby("VESSEL ID")["ARRIVAL DATE"].shift(-1)

    transits = (prochaine_arrivee - df["SAILING DATE"]).dt.days.dropna()
    return transits[transits >= 0]


def tracer_distribution(year=2002, save=True, verbose=True):
    transits = durees_transit(year)
    bas, haut = CREUX

    if verbose:
        print(f"\n=== DISTRIBUTION DES TRANSITS {year} ===")
        print(f"Transits valides : {len(transits)}")
        print(f"  <= {bas} jours         : {100 * (transits <= bas).mean():.1f} %")
        print(
            f"  entre {bas} et {haut} jours : "
            f"{100 * transits.between(bas, haut).mean():.1f} %"
        )
        print(f"  > {haut} jours         : {100 * (transits > haut).mean():.1f} %")
        print("\nPart des transits conserves selon le seuil retenu :")
        for seuil in [15, 20, 30, 40, 45, 55]:
            print(f"  delta_t = {seuil:2d} j -> {100 * (transits <= seuil).mean():.2f} %")

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.axvspan(bas, haut, color="#cccccc", alpha=0.35, lw=0,
               label=f"zone creuse ({bas}-{haut} j) : le seuil y est indifférent")
    ax.hist(transits[transits <= 90], bins=90, color="#4a7ba7",
            edgecolor="white", linewidth=0.3)
    ax.axvline(DELTA_T_DAYS, color="#b2182b", ls="--", lw=1.8,
               label=f"Δt retenu = {DELTA_T_DAYS} j")

    # Les deux bosses correspondent aux trous de collecte : un navire vu avant
    # et après un mois manquant produit un transit fictif de la durée du trou.
    for jour, texte in [(31, "trou d'1 mois\n(novembre)"),
                        (63, "trous de 2 mois\n(avr-mai, juil-août)")]:
        ax.annotate(texte, xy=(jour, 1900), xytext=(jour + 4, 12000),
                    arrowprops=dict(arrowstyle="->", color="#7a3b3b", lw=1.2),
                    fontsize=9, color="#7a3b3b")

    # L'échelle log est indispensable : 82 % des transits tiennent dans les 5 premiers jours
    ax.set_yscale("log")
    ax.set_xlim(0, 90)
    ax.set_xlabel("Durée de transit (jours)")
    ax.set_ylabel("Nombre de trajets (échelle log)")
    ax.set_title(
        f"Distribution des durées de transit {year} — où couper Δt ?"
    )
    ax.grid(alpha=0.3, axis="y")
    ax.legend(loc="upper right", framealpha=0.9)
    plt.tight_layout()

    if save:
        sortie = FIGURES_DIR / f"distribution_transits_{year}.png"
        plt.savefig(sortie, dpi=160)
        if verbose:
            print(f"\nFigure enregistree : {sortie}")
    plt.close()

    return transits


if __name__ == "__main__":
    tracer_distribution(year=2002)
