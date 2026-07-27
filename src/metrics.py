import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx


def calculer_densite_temporelle(inclure_intra=True, save=True, verbose=True):
    base_dir = Path(__file__).resolve().parent.parent
    stream_path = base_dir / "data_clean" / "stream_graph_2010.csv"
    output_path = base_dir / "data_clean" / "densite_temporelle_2010.csv"

    # Charger le Stream Graph
    df = pd.read_csv(stream_path)
    df["SAILING DATE"] = pd.to_datetime(df["SAILING DATE"])
    df["NEXT_ARRIVAL_DATE"] = pd.to_datetime(df["NEXT_ARRIVAL_DATE"])

    # Option : exclure les liens intra-cluster (cabotage local) pour ne garder
    # que la connectivité entre zones distinctes
    if not inclure_intra:
        df = df[~df["INTRA_CLUSTER"]].copy()

    if verbose:
        print(f"Liens utilisés pour δ(t) : {len(df)} "
              f"({'avec' if inclure_intra else 'sans'} intra-cluster)")

    # Étape 1 : table des départs (+1 le jour du départ)
    departs = pd.DataFrame({
        "jour": df["SAILING DATE"],
        "variation": 1
    })

    # Étape 2 : table des arrivées (-1 le lendemain de l'arrivée)
    arrivees = pd.DataFrame({
        "jour": df["NEXT_ARRIVAL_DATE"] + pd.Timedelta(days=1),
        "variation": -1
    })

    # Étape 3 : empiler les événements
    evenements = pd.concat([departs, arrivees])

    # Étape 4 : variation nette par jour
    variation_par_jour = evenements.groupby("jour")["variation"].sum()

    # Étape 5 : trier chronologiquement
    variation_par_jour = variation_par_jour.sort_index()

    # Étape 6 : somme cumulée = densité δ(t)
    densite = variation_par_jour.cumsum()

    # Combler les jours sans événement pour avoir une série continue
    plage_complete = pd.date_range(start=densite.index.min(), end=densite.index.max(), freq="D")
    densite = densite.reindex(plage_complete).ffill()

    if save:
        densite.to_csv(output_path, header=["densite"])
        if verbose:
            print(f"✓ Densité temporelle sauvegardée : {output_path}")

    # Visualisation de la densité des liens actifs à l'instant T
    plt.figure(figsize=(14, 5))
    densite.plot()
    plt.xlabel("Date")
    plt.ylabel("Nombre de liens actifs δ(t)")
    plt.title("Densité temporelle du réseau maritime 2010")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

    return densite

    # =============================================================================
# 3. MÉTRIQUE 2 : COMPOSANTES CONNEXES HEBDOMADAIRES G_Δ
# =============================================================================


from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd


def analyser_composantes_connexes(df, save=True, verbose=True):
    base_dir = Path(__file__).resolve().parent.parent
    output_path = base_dir / "data_clean" / "composantes_connexes_2010.csv"

    # Étape 1 : créer une colonne "semaine"
   # df["semaine"] = (
      #  df["SAILING DATE"].dt.to_period("2W").apply(lambda r: r.start_time)
    #)
    date_min = df["SAILING DATE"].min()
    df["semaine"] = date_min + pd.to_timedelta(
    ((df["SAILING DATE"] - date_min).dt.days // 14) * 14, unit="D"
)

    # Étape 2 : filtrer uniquement les liens inter-cluster
    df_inter = df[~df["INTRA_CLUSTER"]]

    # Étape 3 : boucle par semaine
    resultats = []
    for semaine, groupe in df_inter.groupby("semaine"):
        # Vectorisé avec NetworkX (remplace avantageusement iterrows)
        G = nx.from_pandas_edgelist(
            groupe, source="SOURCE_CLUSTER_ID", target="TARGET_CLUSTER_ID"
        )

        nb_noeuds = G.number_of_nodes()
        composantes = list(nx.connected_components(G))
        nb_composantes = len(composantes)
        plus_grosse = max(len(c) for c in composantes) if composantes else 0

        # Affichage conditionnel (correction du bug d'indentation)
        if verbose and nb_noeuds > 100:
            ratio = (100 * plus_grosse // nb_noeuds) if nb_noeuds > 0 else 0
            print(
                f"{semaine.strftime('%Y-%m-%d')} : {nb_noeuds} nœuds, "
                f"plus grosse composante = {plus_grosse} ({ratio}%)"
            )

        # On sauvegarde toutes les métriques utiles dans le dictionnaire
        resultats.append(
            {
                "semaine": semaine,
                "nb_composantes": nb_composantes,
                "nb_noeuds": nb_noeuds,
                "taille_composante_geante": plus_grosse,
                "ratio_composante_geante": (
                    plus_grosse / nb_noeuds if nb_noeuds > 0 else 0
                ),
            }
        )

    df_resultats = pd.DataFrame(resultats)

    if save:
        df_resultats.to_csv(output_path, index=False)

    # Étape 4 : tracer l'évolution
    plt.figure(figsize=(14, 5))
    plt.plot(
        df_resultats["semaine"].astype(str),
        df_resultats["nb_composantes"],
        marker="o",
        label="Nb composantes",
    )
    plt.xticks(rotation=45)
    plt.xlabel("Semaine")
    plt.ylabel("Nombre de composantes connexes")
    plt.title("Fragmentation du réseau maritime 2010")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

    return df_resultats


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    stream_path = base_dir / "data_clean" / "stream_graph_2010.csv"

    df = pd.read_csv(stream_path)
    df["SAILING DATE"] = pd.to_datetime(df["SAILING DATE"])

    analyser_composantes_connexes(df)