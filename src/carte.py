import math
import pandas as pd
import folium
import searoute as sr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from src.config import DATA_CLEAN_DIR
from src.analyse_greve_2002 import charger, part_du_mondial, moyenne_sur_mois

PORTS_ILWU = [7597, 4977, 7598, 5605, 5263, 4489, 238, 2715, 4777]

AVANT = ("2002-09-25", "2002-09-28")
PENDANT = ("2002-10-01", "2002-10-08")


# ---------------------------------------------------------------- routes

cache_routes = {}


def route_maritime(lon1, lat1, lon2, lat2):
    """Route maritime réelle entre deux points, en [[lat, lon], ...]."""
    cle = (round(lon1, 2), round(lat1, 2), round(lon2, 2), round(lat2, 2))

    if cle in cache_routes:
        return cache_routes[cle]

    try:
        route = sr.searoute((lon1, lat1), (lon2, lat2))
        points = route["geometry"]["coordinates"]
        chemin = [[p[1], p[0]] for p in points]
    except Exception:
        chemin = None

    cache_routes[cle] = chemin
    return chemin


# ---------------------------------------------------------------- données

def coordonnees_clusters(annee=2002):
    """Coordonnées du port le plus fréquenté de chaque cluster.

    On prend le port dominant plutôt que la moyenne des ports : un centroïde
    peut tomber en pleine terre et rendre la route maritime incalculable.
    """
    clusters = pd.read_parquet(DATA_CLEAN_DIR / f"ports_clustered_{annee}.parquet")
    clusters = clusters.dropna(subset=["X1", "Y1"])
    clusters = clusters.sort_values("FREQUENTATION", ascending=False)
    coords = clusters.groupby("Cluster_ID")[["X1", "Y1"]].first()
    return coords


def clusters_cote_ouest(annee=2002):
    """Cluster_ID des 9 ports ILWU."""
    clusters = pd.read_parquet(DATA_CLEAN_DIR / f"ports_clustered_{annee}.parquet")
    selection = clusters[clusters["PLACE ID"].isin(PORTS_ILWU)]
    return set(selection["Cluster_ID"].dropna())


def trafic_par_liaison(annee, debut, fin):
    """Nombre de navires par jour sur chaque liaison, pendant une période.

    Retourne un dictionnaire : (cluster_depart, cluster_arrivee) -> navires/jour
    """
    sg = pd.read_parquet(DATA_CLEAN_DIR / f"stream_graph_{annee}.parquet")
    sg["SAILING DATE"] = pd.to_datetime(sg["SAILING DATE"])

    cibles = clusters_cote_ouest(annee)
    touche_cote_ouest = (sg["SOURCE_CLUSTER_ID"].isin(cibles)
                         | sg["TARGET_CLUSTER_ID"].isin(cibles))
    sg = sg[touche_cote_ouest]
    sg = sg[~sg["INTRA_CLUSTER"]]

    fenetre = sg[(sg["SAILING DATE"] >= debut) & (sg["SAILING DATE"] <= fin)]

    comptes = fenetre.groupby(["SOURCE_CLUSTER_ID", "TARGET_CLUSTER_ID"]).size()

    nb_jours = (pd.Timestamp(fin) - pd.Timestamp(debut)).days + 1

    trafic = {}
    for (source, cible), nb_navires in comptes.items():
        trafic[(source, cible)] = nb_navires / nb_jours

    return trafic


# ---------------------------------------------------------------- carte

def construire_carte(annee=2002, sortie="carte_greve_2002.html"):
    """Carte des liaisons ayant reculé (rouge) ou progressé (vert) pendant la grève."""
    coords = coordonnees_clusters(annee)
    ports_ilwu = clusters_cote_ouest(annee)

    trafic_avant = trafic_par_liaison(annee, AVANT[0], AVANT[1])
    trafic_pendant = trafic_par_liaison(annee, PENDANT[0], PENDANT[1])

    toutes_liaisons = set(trafic_avant) | set(trafic_pendant)
    print(f"{len(toutes_liaisons)} liaisons au total")

    carte = folium.Map(location=[20, -160], zoom_start=3, tiles="cartodbdark_matter")

    nb_traces = 0
    nb_echecs = 0

    for source, cible in toutes_liaisons:
        if source not in coords.index or cible not in coords.index:
            continue

        avant = trafic_avant.get((source, cible), 0)
        pendant = trafic_pendant.get((source, cible), 0)
        variation = pendant - avant

        # On ignore les liaisons dont le trafic a peu bougé
        if abs(variation) < 0.05:
            continue

        lon1 = coords.loc[source, "X1"]
        lat1 = coords.loc[source, "Y1"]
        lon2 = coords.loc[cible, "X1"]
        lat2 = coords.loc[cible, "Y1"]

        chemin = route_maritime(lon1, lat1, lon2, lat2)
        if chemin is None:
            nb_echecs += 1
            continue

        if variation < 0:
            couleur = "#e31a1c"   # rouge : le trafic a baissé
        else:
            couleur = "#33a02c"   # vert : le trafic a augmenté

        # Racine carrée : sans elle, les petites liaisons sont invisibles
        epaisseur = 1.2 + math.sqrt(abs(variation)) * 4
        epaisseur = min(epaisseur, 10)

        texte = f"{avant:.2f} → {pendant:.2f} navires/jour"

        trait = folium.PolyLine(
            locations=chemin,
            color=couleur,
            weight=epaisseur,
            opacity=0.75,
            popup=texte,
        )
        trait.add_to(carte)
        nb_traces += 1

    # Les 9 ports ILWU en jaune
    for cluster_id in ports_ilwu:
        if cluster_id not in coords.index:
            continue
        marqueur = folium.CircleMarker(
            location=[coords.loc[cluster_id, "Y1"], coords.loc[cluster_id, "X1"]],
            radius=6,
            color="#ffffff",
            weight=1.5,
            fill=True,
            fill_color="#ffdd00",
            fill_opacity=1,
        )
        marqueur.add_to(carte)

    titre = """
    <div style="position:fixed; top:14px; left:60px; z-index:9999; max-width:520px;
                background:rgba(15,15,15,0.9); color:#eee; padding:12px 18px;
                border-radius:6px; font-family:sans-serif;">
      <b style="font-size:16px;">Grève des dockers, côte ouest américaine — octobre 2002</b>
      <div style="font-size:12.5px; line-height:1.5; margin-top:6px; opacity:0.85;">
        Évolution du trafic entre le 25-28 septembre et le 1-8 octobre<br>
        <span style="color:#e31a1c;">&#9473;&#9473;</span> liaison en recul &nbsp;
        <span style="color:#33a02c;">&#9473;&#9473;</span> liaison en hausse<br>
        Épaisseur proportionnelle à l'ampleur du changement<br>
        Points jaunes : les 9 ports concernés par la grève
      </div>
    </div>
    """
    carte.get_root().html.add_child(folium.Element(titre))

    carte.save(sortie)
    print(f"{nb_traces} liaisons tracées, {nb_echecs} routes introuvables")
    print(f"Carte enregistrée : {sortie}")


# ---------------------------------------------------------------- figure

def figure_signal(annee=2002, sortie="signal_greve_2002.png"):
    part = part_du_mondial(charger(annee), PORTS_ILWU)
    idx = pd.to_datetime(part.index)

    ref = moyenne_sur_mois(part, [2, 3, 6])
    sigma = part[idx.month.isin([2, 3, 6])].std()

    m = (idx >= "2002-09-20") & (idx <= "2002-10-20")
    dates, valeurs = idx[m], part[m].values

    fig, ax = plt.subplots(figsize=(13, 5.5))
    ax.axhspan(ref - sigma, ref + sigma, color="grey", alpha=0.15,
               label=f"Régime normal ({ref:.2f}% ± {sigma:.2f})")
    ax.axhline(ref, color="grey", ls="--", lw=1)
    ax.axvspan(pd.Timestamp("2002-09-29"), pd.Timestamp("2002-10-09"),
               color="#b2182b", alpha=0.10, label="Grève (29 sept – 9 oct)")
    # moyenne mobile 3 jours, tracée par-dessus les points
    lissee = pd.Series(valeurs, index=dates).rolling(3, center=True).mean()
    ax.plot(dates, valeurs, color="#0a3069", lw=0.9, marker="o", ms=3.5, alpha=0.45)
    ax.plot(dates, lissee, color="#08306b", lw=2.6)

    ax.annotate("8 jours consécutifs sous le régime normal",
                xy=(pd.Timestamp("2002-10-04"), 0.45),
                xytext=(pd.Timestamp("2002-09-27"), 0.15),
                arrowprops=dict(arrowstyle="->", color="#b2182b"),
                fontsize=10, color="#b2182b")
    ax.annotate("Rattrapage post-réouverture",
                xy=(pd.Timestamp("2002-10-13"), 1.24),
                xytext=(pd.Timestamp("2002-10-13"), 1.42),
                arrowprops=dict(arrowstyle="->", color="#1a9850"),
                fontsize=10, color="#1a9850", ha="center")

    ax.set_ylabel("Part du trafic maritime mondial (%)")
    ax.set_title("Effondrement puis rattrapage du trafic sur la côte ouest américaine",
                 fontsize=13, pad=12)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(alpha=0.25)
    ax.set_ylim(0, 1.6)

    plt.tight_layout()
    plt.savefig(sortie, dpi=160)
    print(f"Figure enregistrée : {sortie}")


if __name__ == "__main__":
    figure_signal()
    construire_carte()