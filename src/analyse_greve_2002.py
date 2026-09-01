import pandas as pd
from src.config import DATA_CLEAN_DIR, MATCHING_PORTS_FILE

PORTS_ILWU = [7597, 4977, 7598, 5605, 5263, 4489, 238, 2715, 4777]
PORTS_PETROLIERS = [863, 5409, 8082, 7643, 8125, 8084, 8102]

def ports_cote_ouest():
    """Retourne les ID_Lloyds des ports US de la côte ouest (filtre géographique)."""
    matching = pd.read_excel(MATCHING_PORTS_FILE)

    usa = matching[matching["COUNTRY"] == "USA"]
    usa = usa.drop_duplicates(subset="ID_Lloyds")
    usa = usa.dropna(subset=["X1", "Y1"])

    ouest = usa[(usa["X1"] < -117) & (usa["Y1"] > 30) & (usa["Y1"] < 50)]
    return set(ouest["ID_Lloyds"])

def charger(annee):
    """Charge les données nettoyées d'une année."""
    chemin = DATA_CLEAN_DIR / f"stays_basic_info_{annee}_clean.parquet"
    df = pd.read_parquet(chemin)
    df["ARRIVAL DATE"] = pd.to_datetime(df["ARRIVAL DATE"])
    df["jour"] = df["ARRIVAL DATE"].dt.date
    df["mois"] = df["ARRIVAL DATE"].dt.month
    return df


def escales_par_jour(df, place_ids=None):
    """Nombre d'escales par jour. Si place_ids est donné, filtre sur ces ports."""
    if place_ids is not None:
        df = df[df["PLACE ID"].isin(place_ids)]

    compte = df.groupby("jour").size()

    # Rendre visibles les jours à zéro
    tous_les_jours = pd.date_range("2002-01-01", "2002-12-31", freq="D").date
    compte = compte.reindex(tous_les_jours, fill_value=0)
    return compte


def part_du_mondial(df, place_ids):
    """Part (%) du trafic mondial captée par un groupe de ports, jour par jour."""
    mondial = escales_par_jour(df)
    groupe = escales_par_jour(df, place_ids)

    part = 100 * groupe / mondial

    # Écarter les jours non collectés (mois censurés)
    jours_valides = mondial > 500
    part = part[jours_valides]
    return part


def moyenne_sur_mois(serie, liste_mois):
    """Moyenne d'une série sur certains mois."""
    index = pd.to_datetime(serie.index)
    masque = index.month.isin(liste_mois)
    return serie[masque].mean()


def comparer(annee=2002):
    df = charger(annee)

    MOIS_CALMES = [2, 3, 6]

    for nom, ports in [("ILWU (conteneurs)", PORTS_ILWU),
                       ("Pétroliers (témoin)", PORTS_PETROLIERS)]:

        part = part_du_mondial(df, ports)

        # Moyenne en période calme
        moy_calme = moyenne_sur_mois(part, MOIS_CALMES)

        # Moyenne pendant la greve (1-8 octobre)
        index = pd.to_datetime(part.index)
        est_greve = (index.month == 10) & (index.day <= 8)
        moy_greve = part[est_greve].mean()

        ratio = moy_greve / moy_calme

        print(f"\n{nom}")
        print(f"  part mois calmes : {moy_calme:.3f}%")
        print(f"  part greve     : {moy_greve:.3f}%")
        print(f"  variation        : {100 * (ratio - 1):+.0f}%")


def detail_greve(annee=2002):
    """Affiche le détail jour par jour autour de la greve."""
    df = charger(annee)

    mondial = escales_par_jour(df)
    ouest = escales_par_jour(df, PORTS_ILWU)
    part = 100 * ouest / mondial

    tableau = pd.DataFrame({
        "mondial": mondial,
        "cote_ouest": ouest,
        "part_%": part.round(2),
    })

    debut = pd.Timestamp("2002-09-25").date()
    fin = pd.Timestamp("2002-10-15").date()
    zoom = tableau.loc[debut:fin]

    print(zoom.to_string())

def tester_robustesse(annee=2002):
    df = charger(annee)
    MOIS_CALMES = [2, 3, 6]

    # Récupérer tous les ports côte ouest actifs, triés par trafic
    ids = ports_cote_ouest()
    actifs = df[df["PLACE ID"].isin(ids)].groupby("PLACE ID").size()
    actifs = actifs.sort_values(ascending=False)

    definitions = {
        "Top 5":  actifs.head(5).index.tolist(),
        "Top 9 (retenu)": PORTS_ILWU,
        "Top 15": actifs.head(15).index.tolist(),
        "Top 30": actifs.head(30).index.tolist(),
        "Tous (48)": actifs.index.tolist(),
    }

    for nom, ports in definitions.items():
        part = part_du_mondial(df, ports)
        moy_calme = moyenne_sur_mois(part, MOIS_CALMES)

        index = pd.to_datetime(part.index)
        est_greve = (index.month == 10) & (index.day <= 8)
        moy_greve = part[est_greve].mean()

        print(f"{nom:18s} : {len(ports):3d} ports, "
              f"calme {moy_calme:.3f}% → greve {moy_greve:.3f}%  "
              f"({100*(moy_greve/moy_calme - 1):+.0f}%)")


<<<<<<< Updated upstream
=======
def mouvements_par_jour(df, place_ids, colonne, plage):
    """Compte par jour des mouvements d'un groupe de ports, sur une date donnée.

    `colonne` vaut "ARRIVAL DATE" pour les arrivées, "SAILING DATE" pour les départs.
    """
    sous_ensemble = df[df["PLACE ID"].isin(place_ids)]
    jours = pd.to_datetime(sous_ensemble[colonne]).dt.normalize()
    return sous_ensemble.groupby(jours).size().reindex(plage, fill_value=0)


def figure_departs_arrivees(annee=2002, save=True, verbose=True):
    """Oppose le rythme des départs et des arrivées aux ports ILWU.

    Les départs cessent le jour même de la fermeture. Les arrivées, elles,
    se maintiennent plusieurs jours : les navires déjà en mer poursuivent leur
    route et viennent mouiller au large. L'écart entre les deux courbes mesure
    le délai de propagation de la perturbation dans le réseau.
    """
    df = charger(annee)
    plage = pd.date_range(*FENETRE_FIGURE, freq="D")

    arrivees = mouvements_par_jour(df, PORTS_ILWU, "ARRIVAL DATE", plage)
    departs = mouvements_par_jour(df, PORTS_ILWU, "SAILING DATE", plage)

    # Regime de reference : la periode couverte precedant la fermeture
    avant = plage < pd.Timestamp(FERMETURE[0])
    fermeture = (plage >= pd.Timestamp(FERMETURE[0])) & (
        plage <= pd.Timestamp(FERMETURE[1])
    )
    ref_arr, ref_dep = arrivees[avant].mean(), departs[avant].mean()

    if verbose:
        print(f"\n=== DEPARTS VS ARRIVEES, PORTS ILWU {annee} ===")
        print(f"Regime de reference ({FENETRE_FIGURE[0]} au 26 septembre) :")
        print(f"  arrivees : {ref_arr:.1f}/jour     departs : {ref_dep:.1f}/jour")
        print("Pendant la fermeture :")
        print(
            f"  arrivees : {arrivees[fermeture].mean():.1f}/jour "
            f"({100 * (arrivees[fermeture].mean() / ref_arr - 1):+.0f} %)"
        )
        print(
            f"  departs  : {departs[fermeture].mean():.1f}/jour "
            f"({100 * (departs[fermeture].mean() / ref_dep - 1):+.0f} %)"
        )

    fig, ax = plt.subplots(figsize=(13, 5.5))

    ax.axvspan(pd.Timestamp(FERMETURE[0]), pd.Timestamp(FERMETURE[1]),
               color="#b2182b", alpha=0.10, lw=0,
               label="Lock-out (27 sept - 8 oct)")
    ax.axhline(ref_arr, color="#0a3069", ls=":", lw=1, alpha=0.6)
    ax.axhline(ref_dep, color="#b35806", ls=":", lw=1, alpha=0.6)

    lisse = {}
    for serie, couleur, etiquette in [
        (arrivees, "#0a3069", "Arrivées"),
        (departs, "#b35806", "Départs"),
    ]:
        lisse[etiquette] = serie.rolling(3, center=True).mean()
        ax.plot(plage, serie.values, color=couleur, lw=0.7, marker="o", ms=2.5, alpha=0.22)
        ax.plot(plage, lisse[etiquette].values, color=couleur, lw=2.6, label=etiquette)

    # a priori L'ecart entre les deux courbes est le stock de navires immobilises :
    # ils sont arrives mais n'ont pas pu repartir.
    ax.fill_between(plage, lisse["Départs"], lisse["Arrivées"],
                    where=lisse["Arrivées"] > lisse["Départs"],
                    color="#b2182b", alpha=0.18, lw=0,
                    label="navires arrivés mais non repartis")

    ax.annotate(
        f"Pendant la fermeture :\ndéparts {100 * (departs[fermeture].mean() / ref_dep - 1):+.0f} %"
        f"   arrivées {100 * (arrivees[fermeture].mean() / ref_arr - 1):+.0f} %",
        xy=(pd.Timestamp("2002-10-02"), 24), xytext=(pd.Timestamp("2002-09-06"), 7),
        arrowprops=dict(arrowstyle="->", color="#7a3b3b", lw=1.2),
        fontsize=10, color="#7a3b3b",
    )
    ax.annotate("rattrapage", xy=(pd.Timestamp("2002-10-13"), 50),
                xytext=(pd.Timestamp("2002-10-15"), 62),
                arrowprops=dict(arrowstyle="->", color="#1a7a3c"),
                fontsize=10, color="#1a7a3c")

    ax.set_ylim(0, 70)
    ax.set_xlim(plage[0], plage[-1])
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.set_ylabel("Mouvements par jour")
    ax.set_title(
        "Ports ILWU 2002 : les départs décrochent avant les arrivées, et deux fois plus fort",
        fontsize=12.5, pad=12,
    )
    ax.grid(alpha=0.25)
    ax.legend(loc="lower right", framealpha=0.92, fontsize=9)
    plt.tight_layout()

    if save:
        sortie = FIGURES_DIR / f"departs_arrivees_ilwu_{annee}.png"
        plt.savefig(sortie, dpi=160)
        if verbose:
            print(f"\nFigure enregistree : {sortie}")
    plt.close()

    return pd.DataFrame({"arrivees": arrivees, "departs": departs})


>>>>>>> Stashed changes
if __name__ == "__main__":
    detail_greve()
    comparer()
    tester_robustesse()