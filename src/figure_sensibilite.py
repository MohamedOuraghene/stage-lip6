"""Sensibilité du clustering spatial à ses deux paramètres.

Fait varier conjointement le rayon d'agrégation et le seuil de nœud autonome,
et trace le nombre de zones obtenu. Sert à montrer que le rayon commande le
résultat alors que le seuil est quasiment sans effet.

À lancer depuis la racine du projet : python -m src.figure_sensibilite
"""

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle

from src.cluster import prepare_ports_for_clustering
from src.config import FIGURES_DIR, POURCENTAGE_SEUIL_HUB, RAYON_MAX_KM

RAYONS = [30, 44, 75, 100, 150]
SEUILS = [0.001, 0.005, 0.01, 0.02]


def matrice_sensibilite(year=2002, rayons=RAYONS, seuils=SEUILS, verbose=True):
    """Relance le clustering pour chaque couple (rayon, seuil)."""
    lignes = []
    for rayon in rayons:
        for seuil in seuils:
            ports = prepare_ports_for_clustering(
                year=year,
                rayon_km=rayon,
                pourcentage_seuil=seuil,
                save=False,
                verbose=False,
            )
            if ports is None:
                continue
            nb_points = ports["PLACE ID"].nunique()
            nb_zones = ports["Cluster_ID"].nunique()
            lignes.append({
                "rayon": rayon,
                "seuil": seuil * 100,
                "zones": nb_zones,
                "reduction": (nb_points - nb_zones) / nb_points * 100,
            })
            if verbose:
                print(f"  rayon {rayon:3d} km, seuil {seuil * 100:.1f} % "
                      f"-> {nb_zones} zones")

    return pd.DataFrame(lignes)


def tracer_matrice(year=2002, save=True, verbose=True):
    if verbose:
        print(f"\n=== MATRICE DE SENSIBILITE DU CLUSTERING {year} ===")
        print(f"{len(RAYONS) * len(SEUILS)} combinaisons a calculer, patientez.\n")

    res = matrice_sensibilite(year=year, verbose=verbose)
    zones = res.pivot(index="rayon", columns="seuil", values="zones")
    reduction = res.pivot(index="rayon", columns="seuil", values="reduction")

    if verbose:
        print("\nNombre de zones :")
        print(zones.to_string())

    fig, (ax_carte, ax_courbes) = plt.subplots(
        1, 2, figsize=(13.5, 5.2), gridspec_kw={"width_ratios": [1.15, 1]}
    )

    image = ax_carte.imshow(zones.values, cmap="YlGnBu", aspect="auto")

    bascule = zones.values.min() + 0.55 * (zones.values.max() - zones.values.min())
    for i, rayon in enumerate(zones.index):
        for j, seuil in enumerate(zones.columns):
            valeur = zones.loc[rayon, seuil]
            clair = valeur > bascule
            ax_carte.text(
                j, i - 0.13, f"{valeur:,}".replace(",", " "),
                ha="center", va="center", fontsize=11, fontweight="bold",
                color="white" if clair else "#1a1a1a",
            )
            ax_carte.text(
                j, i + 0.22,
                f"−{reduction.loc[rayon, seuil]:.1f} %".replace(".", ","),
                ha="center", va="center", fontsize=8.5,
                color="#e8e8e8" if clair else "#2e2e2e",
            )

    i_ret = list(zones.index).index(int(RAYON_MAX_KM))
    j_ret = list(zones.columns).index(POURCENTAGE_SEUIL_HUB * 100)
    ax_carte.add_patch(Rectangle(
        (j_ret - 0.5, i_ret - 0.5), 1, 1,
        fill=False, edgecolor="#b2182b", lw=2.8,
    ))

    ax_carte.set_xticks(range(len(zones.columns)))
    ax_carte.set_xticklabels([f"{s:g} %".replace(".", ",") for s in zones.columns])
    ax_carte.set_yticks(range(len(zones.index)))
    ax_carte.set_yticklabels([f"{r} km" for r in zones.index])
    ax_carte.set_xlabel("Seuil de nœud autonome (% du trafic mondial)")
    ax_carte.set_ylabel("Rayon d'agrégation")
    ax_carte.set_title(
        "Nombre de zones obtenues\n(en petit : réduction de complexité)",
        fontsize=11, pad=10,
    )
    fig.colorbar(image, ax=ax_carte, label="zones", fraction=0.046, pad=0.03)

    for seuil in zones.columns:
        ax_courbes.plot(
            zones.index, zones[seuil].values,
            marker="o", ms=5, lw=1.8,
            label=f"seuil {seuil:g} %".replace(".", ","),
        )

    valeur_retenue = zones.loc[int(RAYON_MAX_KM), POURCENTAGE_SEUIL_HUB * 100]
    ax_courbes.scatter(
        [RAYON_MAX_KM], [valeur_retenue],
        s=160, facecolors="none", edgecolors="#b2182b", lw=2.5, zorder=5,
    )
    ax_courbes.annotate(
        f"retenu : {int(RAYON_MAX_KM)} km, "
        f"{POURCENTAGE_SEUIL_HUB * 100:g} %".replace(".", ","),
        xy=(RAYON_MAX_KM, valeur_retenue), xytext=(62, 2680),
        arrowprops=dict(arrowstyle="->", color="#b2182b", lw=1.3),
        fontsize=9.5, color="#b2182b",
    )
    ax_courbes.annotate(
        "les quatre courbes sont presque confondues :\n"
        "le seuil ne déplace le résultat que de 4 %",
        xy=(150, zones.loc[150].mean()), xytext=(84, 2050),
        arrowprops=dict(arrowstyle="->", color="#555555", lw=1.1),
        fontsize=9.5, color="#333333",
    )

    ax_courbes.set_xlabel("Rayon d'agrégation (km)")
    ax_courbes.set_ylabel("Nombre de zones")
    ax_courbes.set_title(
        "Le rayon commande le résultat, pas le seuil", fontsize=11, pad=10
    )
    ax_courbes.grid(alpha=0.3)
    ax_courbes.legend(fontsize=9, framealpha=0.9)

    fig.suptitle(
        f"Sensibilité du clustering spatial à ses paramètres ({year})",
        fontsize=13, y=0.99,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    if save:
        sortie = FIGURES_DIR / f"sensibilite_clustering_{year}.png"
        plt.savefig(sortie, dpi=160)
        if verbose:
            print(f"\nFigure enregistree : {sortie}")
    plt.close()

    return zones, reduction


if __name__ == "__main__":
    tracer_matrice(year=2002)
