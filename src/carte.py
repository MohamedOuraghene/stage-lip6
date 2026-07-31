import pandas as pd
import folium
from src.config import DATA_CLEAN_DIR

PORTS_ILWU = [7597, 4977, 7598, 5605, 5263, 4489, 238, 2715, 4777]

PERIODES = {
    "Avant (25-28 sept)":   ("2002-09-25", "2002-09-28"),
    "Pendant (1-8 oct)":    ("2002-10-01", "2002-10-08"),
    "Apres (12-14 oct)":    ("2002-10-12", "2002-10-14"),
}
COULEURS = {"Avant (25-28 sept)": "#2166ac",
            "Pendant (1-8 oct)":  "#b2182b",
            "Apres (12-14 oct)":  "#1a9850"}


def coordonnees_clusters(annee=2002):
    """Une coordonnée par cluster : la moyenne de ses ports."""
    clusters = pd.read_parquet(DATA_CLEAN_DIR / f"ports_clustered_{annee}.parquet")
    coords = clusters.groupby("Cluster_ID")[["X1", "Y1"]].mean().dropna()
    return coords


def clusters_cote_ouest(annee=2002):
    """Cluster_ID correspondant aux ports ILWU."""
    clusters = pd.read_parquet(DATA_CLEAN_DIR / f"ports_clustered_{annee}.parquet")
    sel = clusters[clusters["PLACE ID"].isin(PORTS_ILWU)]
    return set(sel["Cluster_ID"].dropna())


def liens_agreges(annee=2002):
    """Charge le stream graph et agrège par paire de clusters et par période."""
    sg = pd.read_parquet(DATA_CLEAN_DIR / f"stream_graph_{annee}.parquet")
    sg["SAILING DATE"] = pd.to_datetime(sg["SAILING DATE"])

    cibles = clusters_cote_ouest(annee)

    # Ne garder que les liens touchant la côte ouest, hors intra-cluster
    touche = sg["SOURCE_CLUSTER_ID"].isin(cibles) | sg["TARGET_CLUSTER_ID"].isin(cibles)
    sg = sg[touche & ~sg["INTRA_CLUSTER"]]

    resultats = {}
    for nom, (debut, fin) in PERIODES.items():
        fenetre = sg[(sg["SAILING DATE"] >= debut) & (sg["SAILING DATE"] <= fin)]
        agrege = (fenetre.groupby(["SOURCE_CLUSTER_ID", "TARGET_CLUSTER_ID"])
                         .size()
                         .reset_index(name="NB_NAVIRES"))
        nb_jours = (pd.Timestamp(fin) - pd.Timestamp(debut)).days + 1
        agrege["NAVIRES_PAR_JOUR"] = agrege["NB_NAVIRES"] / nb_jours
        resultats[nom] = agrege
        print(f"{nom:22s} : {len(fenetre)} liens -> {len(agrege)} traits")

    return resultats


def construire_carte(annee=2002, sortie="carte_greve_2002.html"):
    coords = coordonnees_clusters(annee)
    periodes = liens_agreges(annee)

    carte = folium.Map(location=[35, -150], zoom_start=3, tiles="CartoDB positron")

    for nom, liens in periodes.items():
        couche = folium.FeatureGroup(name=nom, show=(nom.startswith("Pendant")))

        for _, ligne in liens.iterrows():
            src, dst = ligne["SOURCE_CLUSTER_ID"], ligne["TARGET_CLUSTER_ID"]
            if src not in coords.index or dst not in coords.index:
                continue

            folium.PolyLine(
                locations=[
                    [coords.loc[src, "Y1"], coords.loc[src, "X1"]],
                    [coords.loc[dst, "Y1"], coords.loc[dst, "X1"]],
                ],
                color=COULEURS[nom],
                weight=min(1 + ligne["NAVIRES_PAR_JOUR"] * 2, 8),
                popup=f"{ligne['NAVIRES_PAR_JOUR']:.1f} navires/jour",
                opacity=0.5,
            ).add_to(couche)

        couche.add_to(carte)

    folium.LayerControl(collapsed=False).add_to(carte)
    carte.save(sortie)
    print(f"\nCarte enregistree : {sortie}")


if __name__ == "__main__":
    construire_carte()