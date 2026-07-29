from pathlib import Path
import pandas as pd
from config import DATA_CLEAN_DIR, MATCHING_PORTS_FILE


def trouver_ports_cote_ouest():
    """Étape exploratoire : identifier les PLACE ID des ports US de la côte ouest."""
    matching = pd.read_excel(MATCHING_PORTS_FILE)

    # Tous les ports américains avec leurs coordonnées
    usa = matching[matching["COUNTRY"] == "USA"][
        ["ID_Lloyds", "Name_Final", "Type", "X1", "Y1"]
    ].drop_duplicates(subset="ID_Lloyds").dropna(subset=["X1", "Y1"])

    # La côte ouest = longitude très négative (Pacifique), hors Alaska/Hawaii
    ouest = usa[(usa["X1"] < -117) & (usa["Y1"] > 30) & (usa["Y1"] < 50)]

    print(f"Ports US totaux : {len(usa)}")
    print(f"Candidats côte ouest (lon < -117, lat 30-50) : {len(ouest)}\n")
    print(ouest.sort_values("Y1").to_string(index=False))

    return ouest

def ports_cote_ouest_actifs(annee=2002, n_top=20):
    """Croise le filtre géographique avec le trafic réellement observé."""
    ouest = trouver_ports_cote_ouest()          # tes 211 candidats
    ids_ouest = set(ouest["ID_Lloyds"]) # ensemble plutot que liste car c'est en o(1) pour le test d'appartenance

    df = pd.read_csv(DATA_CLEAN_DIR / f"stays_basic_info_{annee}_clean.csv")
    subset = df[df["PLACE ID"].isin(ids_ouest)] # isin est l'équivalent de where PLACE ID in ids_ouest en SQL

    trafic = (subset.groupby(["PLACE ID", "Name_Final", "Type"])
                    .size()                           # .size() compte le nombre de lignes par groupe contrairement à .count() qui compte les valeurs non nulles d'une colonne
                    .sort_values(ascending=False)
                    .reset_index(name="ESCALES"))

    print(f"Ports côte ouest candidats : {len(ouest)}")
    print(f"Ports réellement actifs en {annee} : {len(trafic)}")
    print(f"Escales totales : {trafic['ESCALES'].sum()}\n")
    print(trafic.head(30).to_string(index=False))

    return trafic

PORTS_ILWU_MAJEURS = [7597, 4977, 7598, 5605, 5263, 4489, 238, 2715, 4777]
# Long Beach, LA, Oakland, SF, Tacoma, Seattle, Portland, Vancouver(WA), Richmond

PORTS_PETROLIERS = [863, 5409, 8082, 7643, 8125, 8084, 8102]
# March Point, El Segundo, Martinez, Benicia, Rodeo, Selby, Crockett — groupe témoin


def arrivees_quotidiennes(place_ids, annee=2002, label=""):
    df = pd.read_csv(DATA_CLEAN_DIR / f"stays_basic_info_{annee}_clean.csv")
    df["ARRIVAL DATE"] = pd.to_datetime(df["ARRIVAL DATE"])

    subset = df[df["PLACE ID"].isin(place_ids)]
    quotidien = subset.groupby(subset["ARRIVAL DATE"].dt.date).size()
    plage = pd.date_range("2002-09-15", "2002-10-25", freq="D").date
    quotidien = quotidien.reindex(plage, fill_value=0)

    # Moyennes des mois pleins pour référence
    for mois, nom in [(2, "fév"), (3, "mars"), (6, "juin"), (9, "sept"), (10, "oct"), (12, "déc")]:
        jours = [d for d in quotidien.index if d.month == mois]
        if jours:
            print(f"  {nom} : {quotidien[jours].mean():.1f} escales/jour")

    # Zoom sur la période du lockout
    debut, fin = pd.Timestamp("2002-09-15").date(), pd.Timestamp("2002-10-25").date()
    zoom = quotidien[(quotidien.index >= debut) & (quotidien.index <= fin)]
    print(f"\n=== {label} — jour par jour, 15 sept au 25 oct ===")
    print(zoom.to_string())

    df = pd.read_csv(DATA_CLEAN_DIR / "stays_basic_info_2002_clean.csv")
    df["ARRIVAL DATE"] = pd.to_datetime(df["ARRIVAL DATE"])

    plage = pd.date_range("2002-09-25", "2002-10-15", freq="D")
    mondial = df.groupby(df["ARRIVAL DATE"].dt.date).size().reindex(plage.date, fill_value=0)

    ouest = df[df["PLACE ID"].isin(PORTS_ILWU_MAJEURS)]
    cote_ouest = ouest.groupby(ouest["ARRIVAL DATE"].dt.date).size().reindex(plage.date, fill_value=0)

    comparaison = pd.DataFrame({
        "mondial": mondial,
        "cote_ouest": cote_ouest,
        "part_%": (100 * cote_ouest / mondial).round(2)
    })
    print(comparaison.to_string())

    df["jour"] = df["ARRIVAL DATE"].dt.date
    mondial_j = df.groupby("jour").size()
    ouest_j = df[df["PLACE ID"].isin(PORTS_ILWU_MAJEURS)].groupby("jour").size()
    part = (100 * ouest_j / mondial_j).dropna()

    # uniquement les jours réellement collectés
    part = part[mondial_j.reindex(part.index) > 500]

    calme = part[[d for d in part.index if d.month in (2, 3, 6)]]
    print(f"Référence : {calme.mean():.2f}% ± {calme.std():.2f}")
    print(f"Min-max sur les mois calmes : {calme.min():.2f} – {calme.max():.2f}")

    zeros = mondial_j.reindex(pd.date_range("2002-01-01","2002-12-31",freq="D").date, fill_value=0)
    zeros = zeros[zeros == 0]
    print(f"{len(zeros)} jours sans données en 2002")
    print(zeros.index.tolist())

    return quotidien

def comparer_groupes(annee=2002):
    df = pd.read_csv(DATA_CLEAN_DIR / f"stays_basic_info_{annee}_clean.csv")
    df["ARRIVAL DATE"] = pd.to_datetime(df["ARRIVAL DATE"])
    df["jour"] = df["ARRIVAL DATE"].dt.date

    mondial = df.groupby("jour").size()
    lockout = [d for d in mondial.index if d.month == 10 and 1 <= d.day <= 8]
    calme   = [d for d in mondial.index if d.month in (2, 3, 6)]

    for nom, ids in [("ILWU (conteneurs)", PORTS_ILWU_MAJEURS),
                     ("Pétroliers (témoin)", PORTS_PETROLIERS)]:
        sub  = df[df["PLACE ID"].isin(ids)]
        part = (100 * sub.groupby("jour").size() / mondial).reindex(mondial.index, fill_value=0)
        m_calme, m_lock = part[calme].mean(), part[lockout].mean()
        print(f"\n{nom}")
        print(f"  escales totales : {len(sub)}")
        print(f"  part mois calmes : {m_calme:.3f}%")
        print(f"  part lockout     : {m_lock:.3f}%")
        print(f"  ratio            : {m_lock/m_calme:.2f}  ({100*(m_lock/m_calme-1):+.0f}%)")

def tester_robustesse(annee=2002):
    df = charger(annee)
    MOIS_CALMES = [2, 3, 6]

    # Récupérer tous les ports côte ouest actifs, triés par trafic
    from analyse_greve_2002 import trouver_ports_cote_ouest
    ouest = trouver_ports_cote_ouest()
    ids = set(ouest["ID_Lloyds"])
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
        est_lockout = (index.month == 10) & (index.day <= 8)
        moy_lock = part[est_lockout].mean()

        print(f"{nom:18s} : {len(ports):3d} ports, "
              f"calme {moy_calme:.3f}% → lockout {moy_lock:.3f}%  "
              f"({100*(moy_lock/moy_calme - 1):+.0f}%)")


if __name__ == "__main__":
    tester_robustesse()
