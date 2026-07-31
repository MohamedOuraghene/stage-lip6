from pathlib import Path
import pandas as pd


def reconstruct_stream_graph(
    year=2010, delta_t=30, save=True, verbose=True
):
    base_dir = Path(__file__).resolve().parent.parent
    clean_path = base_dir / "data_clean" / f"stays_basic_info_{year}_clean.parquet"
    clustered_path = base_dir / "data_clean" / f"ports_clustered_{year}.parquet"
    output_path = base_dir / "data_clean" / f"stream_graph_{year}.parquet"

    if not clean_path.exists() or not clustered_path.exists():
        print(
            f"Erreur : Fichiers introuvables pour l'année {year}. Exécute"
            " clean.py et cluster.py d'abord."
        )
        return None

    # 1. Charger les deux fichiers (low_memory=False évite les DtypeWarning)
    df = pd.read_parquet(clean_path)
    clusters = pd.read_parquet(clustered_path)

    df["ARRIVAL DATE"] = pd.to_datetime(df["ARRIVAL DATE"])
    df["SAILING DATE"] = pd.to_datetime(df["SAILING DATE"])

    # 2. Joindre le cluster sur chaque séjour
    corresp = clusters[
        ["PLACE ID", "Cluster_ID", "Cluster_Name"]
    ].drop_duplicates(subset="PLACE ID")
    df = df.merge(corresp, on="PLACE ID", how="left")

    # 3. Trier par navire puis chronologiquement
    df = df.sort_values(["VESSEL ID", "ARRIVAL DATE"])

    # 4. Pour chaque séjour, trouver le cluster suivant du même navire
    df["NEXT_CLUSTER_ID"] = df.groupby("VESSEL ID")["Cluster_ID"].shift(-1)
    df["NEXT_CLUSTER_NAME"] = df.groupby("VESSEL ID")["Cluster_Name"].shift(-1)
    df["NEXT_ARRIVAL_DATE"] = df.groupby("VESSEL ID")["ARRIVAL DATE"].shift(-1)

    # 5. Calculer la durée du transit
    df["TRANSIT_DAYS"] = (
        df["NEXT_ARRIVAL_DATE"] - df["SAILING DATE"]
    ).dt.days

    # 6. Marquer les liens intra-cluster (même cluster au départ et à l'arrivée)
    df["INTRA_CLUSTER"] = df["Cluster_ID"] == df["NEXT_CLUSTER_ID"]

    # 7. Construire les liens candidats (on retire les dernières lignes sans suite)
    liens = df.dropna(subset=["NEXT_CLUSTER_ID"]).copy()

    # 8. Appliquer Δt : un lien est valide si 0 <= transit <= delta_t
    liens_valides = liens[
        (liens["TRANSIT_DAYS"] >= 0) & (liens["TRANSIT_DAYS"] <= delta_t)
    ].copy()

    # 9. Produire le Stream Graph : (temps, cluster source, cluster cible, durée)
    stream_graph = liens_valides[[
        "VESSEL ID",
        "SAILING DATE",  # instant de départ du lien
        "NEXT_ARRIVAL_DATE",  # instant d'arrivée
        "Cluster_ID",  # cluster source
        "Cluster_Name",
        "NEXT_CLUSTER_ID",  # cluster cible
        "NEXT_CLUSTER_NAME",
        "TRANSIT_DAYS",
        "INTRA_CLUSTER",
    ]].rename(
        columns={
            "Cluster_ID": "SOURCE_CLUSTER_ID",
            "Cluster_Name": "SOURCE_CLUSTER_NAME",
            "NEXT_CLUSTER_ID": "TARGET_CLUSTER_ID",
            "NEXT_CLUSTER_NAME": "TARGET_CLUSTER_NAME",
        }
    )

    if verbose:
        total = len(liens)
        valides = len(stream_graph)
        intra = stream_graph["INTRA_CLUSTER"].sum()
        print(
            f"\n=== RECONSTRUCTION STREAM GRAPH {year} (Δt = {delta_t} jours)"
            " ==="
        )
        print(f"Liens candidats (transits existants) : {total}")
        print(f"Liens valides (≤ {delta_t} jours)     : {valides}")
        print(f"  dont intra-cluster : {intra}")
        print(f"  dont inter-cluster : {valides - intra}")
        print(f"Liens coupés par Δt : {total - valides}\n")

        print("Top 10 des clusters avec le plus de transits intra-cluster :")
        intra_df = stream_graph[stream_graph["INTRA_CLUSTER"] == True]
        print(
            intra_df.groupby("SOURCE_CLUSTER_NAME")
            .size()
            .sort_values(ascending=False)
            .head(10)
        )

    if save:
        stream_graph.to_parquet(output_path, index=False)
        if verbose:
            print(f"\n Stream Graph sauvegardé : {output_path}")

    return stream_graph


if __name__ == "__main__":
    for year in [2010, 2002]:
        reconstruct_stream_graph(year=year, delta_t=30)