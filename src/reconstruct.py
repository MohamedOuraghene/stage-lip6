import pandas as pd
from pathlib import Path


def reconstruct_stream_graph(delta_t=30, save=True, verbose=True):
    base_dir = Path(__file__).resolve().parent.parent
    clean_path = base_dir / "data_clean" / "stays_basic_info_2010_clean.csv"
    clustered_path = base_dir / "data_clean" / "ports_clustered_2010.csv"
    output_path = base_dir / "data_clean" / "stream_graph_2010.csv"

    # 1. Charger les deux fichiers
    df = pd.read_csv(clean_path)
    clusters = pd.read_csv(clustered_path)

    df["ARRIVAL DATE"] = pd.to_datetime(df["ARRIVAL DATE"])
    df["SAILING DATE"] = pd.to_datetime(df["SAILING DATE"])

    # 2. Joindre le cluster sur chaque séjour
    # On récupère la correspondance PLACE ID -> Cluster
    corresp = clusters[["PLACE ID", "Cluster_ID", "Cluster_Name"]].drop_duplicates(subset="PLACE ID")
    df = df.merge(corresp, on="PLACE ID", how="left")

    # 3. Trier par navire puis chronologiquement
    df = df.sort_values(["VESSEL ID", "ARRIVAL DATE"])

    # 4. Pour chaque séjour, trouver le cluster suivant du même navire
    df["NEXT_CLUSTER_ID"] = df.groupby("VESSEL ID")["Cluster_ID"].shift(-1)
    df["NEXT_CLUSTER_NAME"] = df.groupby("VESSEL ID")["Cluster_Name"].shift(-1)
    df["NEXT_ARRIVAL_DATE"] = df.groupby("VESSEL ID")["ARRIVAL DATE"].shift(-1)

    # 5. Calculer la durée du transit
    df["TRANSIT_DAYS"] = (df["NEXT_ARRIVAL_DATE"] - df["SAILING DATE"]).dt.days

    # 6. Marquer les liens intra-cluster (même cluster au départ et à l'arrivée)
    df["INTRA_CLUSTER"] = df["Cluster_ID"] == df["NEXT_CLUSTER_ID"]

    # 7. Construire les liens candidats (on retire les dernières lignes sans suite)
    liens = df.dropna(subset=["NEXT_CLUSTER_ID"]).copy()

    # 8. Appliquer Δt : un lien est valide si 0 <= transit <= delta_t
    liens_valides = liens[(liens["TRANSIT_DAYS"] >= 0) & (liens["TRANSIT_DAYS"] <= delta_t)].copy()

    # 9. Produire le Stream Graph : (temps, cluster source, cluster cible, durée)
    stream_graph = liens_valides[[
        "VESSEL ID",
        "SAILING DATE",        # instant de départ du lien
        "NEXT_ARRIVAL_DATE",   # instant d'arrivée
        "Cluster_ID",          # cluster source
        "Cluster_Name",
        "NEXT_CLUSTER_ID",     # cluster cible
        "NEXT_CLUSTER_NAME",
        "TRANSIT_DAYS",
        "INTRA_CLUSTER",
    ]].rename(columns={
        "Cluster_ID": "SOURCE_CLUSTER_ID",
        "Cluster_Name": "SOURCE_CLUSTER_NAME",
        "NEXT_CLUSTER_ID": "TARGET_CLUSTER_ID",
        "NEXT_CLUSTER_NAME": "TARGET_CLUSTER_NAME",
    })

    if verbose:
        total = len(liens)
        valides = len(stream_graph)
        intra = stream_graph["INTRA_CLUSTER"].sum()
        print(f"\n=== RECONSTRUCTION STREAM GRAPH (Δt = {delta_t} jours) ===")
        print(f"Liens candidats (transits existants) : {total}")
        print(f"Liens valides (≤ {delta_t} jours)     : {valides}")
        print(f"  dont intra-cluster : {intra}")
        print(f"  dont inter-cluster : {valides - intra}")
        print(f"Liens coupés par Δt : {total - valides}")

        intra = stream_graph[stream_graph["INTRA_CLUSTER"] == True]
        print(intra.groupby("SOURCE_CLUSTER_NAME").size().sort_values(ascending=False).head(10))

        intra_helsinki = stream_graph[
        (stream_graph["SOURCE_CLUSTER_NAME"] == "Helsinki") &
        (stream_graph["INTRA_CLUSTER"] == True)
            ]
        print(intra_helsinki["TRANSIT_DAYS"].describe())

        clusters = pd.read_csv(base_dir / "data_clean" / "ports_clustered_2010.csv")
        helsinki = clusters[clusters["Cluster_Name"].str.contains("Helsinki", na=False)]
        print(helsinki[["PLACE ID", "Name_Final", "Cluster_ID"]])

    if save:
        stream_graph.to_csv(output_path, index=False)
        if verbose:
            print(f"✓ Stream Graph sauvegardé : {output_path}")

    return stream_graph


if __name__ == "__main__":
    reconstruct_stream_graph(delta_t=30)