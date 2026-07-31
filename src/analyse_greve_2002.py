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


if __name__ == "__main__":
    detail_greve()
    comparer()
    tester_robustesse()