from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

# Redirection vers results/ et reports/figures/ si config.py existe, sinon fallback local
try:
    from src.config import FIGURES_DIR, RESULTS_DIR
except ImportError:
    base_dir = Path(__file__).resolve().parent.parent
    RESULTS_DIR = base_dir / "results"
    FIGURES_DIR = base_dir / "reports" / "figures"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# 1. MÉTRIQUE 1 : DENSITÉ TEMPORELLE δ(t)
# =============================================================================


def calculer_densite_temporelle(
    year=2010, inclure_intra=True, save=True, verbose=True
):
    base_dir = Path(__file__).resolve().parent.parent
    stream_path = base_dir / "data_clean" / f"stream_graph_{year}.parquet"
    output_parquet = RESULTS_DIR / f"densite_temporelle_{year}.parquet"
    output_fig = FIGURES_DIR / f"densite_temporelle_{year}.png"

    if not stream_path.exists():
        print(f"Erreur : Fichier {stream_path.name} introuvable.")
        return None

    # Charger le "stream graph"
    df = pd.read_parquet(stream_path)
    df["SAILING DATE"] = pd.to_datetime(df["SAILING DATE"])
    df["NEXT_ARRIVAL_DATE"] = pd.to_datetime(df["NEXT_ARRIVAL_DATE"])

    # si tu veux exclure les liens intra-cluster 
    if not inclure_intra:
        df = df[~df["INTRA_CLUSTER"]].copy()

    if verbose:
        print(
            f"\n=== DENSITÉ TEMPORELLE {year} ==="
            f"\nLiens utilisés pour δ(t) : {len(df)} "
            f"({'avec' if inclure_intra else 'sans'} intra-cluster)"
        )

    # Étape 1 : table des départs (+1 le jour du départ)
    departs = pd.DataFrame({"jour": df["SAILING DATE"], "variation": 1})

    # Étape 2 : table des arrivées (-1 le lendemain de l'arrivée)
    arrivees = pd.DataFrame(
        {"jour": df["NEXT_ARRIVAL_DATE"] + pd.Timedelta(days=1), "variation": -1}
    )

    # Étape 3 : empiler les événements
    evenements = pd.concat([departs, arrivees])

    # Étape 4 : variation nette par jour
    variation_par_jour = evenements.groupby("jour")["variation"].sum()

    # Étape 5 : trier chronologiquement
    variation_par_jour = variation_par_jour.sort_index()

    # Étape 6 : somme cumulée = densité δ(t)
    densite = variation_par_jour.cumsum()

    # Combler les jours sans événement pour avoir une série continue
    plage_complete = pd.date_range(
        start=densite.index.min(), end=densite.index.max(), freq="D"
    )
    densite = densite.reindex(plage_complete).ffill()

    if save:
        densite.to_frame(name="densite").reset_index(names="jour").to_parquet(output_parquet, index=False)
        if verbose:
            print(f" densité temporelle sauvegardée : {output_parquet}")

    # Visualisation de la densité des liens actifs à l'instant T
    plt.figure(figsize=(14, 5))
    densite.plot()
    plt.xlabel("Date")
    plt.ylabel("Nombre de liens actifs δ(t)")
    plt.title(f"Densité temporelle du réseau maritime {year}")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    if save:
        plt.savefig(output_fig, dpi=300)
        if verbose:
            print(f"✓ Graphique densité sauvegardé : {output_fig}")

    plt.show()

    return densite


# =============================================================================
# 2. MÉTRIQUE 2 : COMPOSANTES CONNEXES HEBDOMADAIRES G_Δ
# =============================================================================


def analyser_composantes_connexes(year=2010, df=None, save=True, verbose=True):
    base_dir = Path(__file__).resolve().parent.parent
    output_csv = RESULTS_DIR / f"composantes_connexes_{year}.csv"
    output_fig = FIGURES_DIR / f"composantes_connexes_{year}.png"

    # Si df n'est pas fourni en argument, on le charge automatiquement
    if df is None:
        stream_path = base_dir / "data_clean" / f"stream_graph_{year}.parquet"
        if not stream_path.exists():
            print(f"Erreur : Fichier {stream_path.name} introuvable.")
            return None
        df = pd.read_parquet(stream_path) # pas de low memory en parquet
        df["SAILING DATE"] = pd.to_datetime(df["SAILING DATE"])

    if verbose:
        print(f"\n=== COMPOSANTES CONNEXES {year} ===")

    # Étape 1 : créer une colonne "semaine" (fenêtres de 14 jours)
    date_min = df["SAILING DATE"].min()
    df["semaine"] = date_min + pd.to_timedelta(
        ((df["SAILING DATE"] - date_min).dt.days // 14) * 14, unit="D"
    )

    # Étape 2 : filtrer uniquement les liens inter-cluster
    df_inter = df[~df["INTRA_CLUSTER"]]

    # Étape 3 : boucle par semaine
    resultats = []
    for semaine, groupe in df_inter.groupby("semaine"):
        G = nx.from_pandas_edgelist(
            groupe, source="SOURCE_CLUSTER_ID", target="TARGET_CLUSTER_ID"
        )

        nb_noeuds = G.number_of_nodes()
        composantes = list(nx.connected_components(G))
        nb_composantes = len(composantes)
        plus_grosse = max(len(c) for c in composantes) if composantes else 0

        if verbose and nb_noeuds > 100:
            ratio = (100 * plus_grosse // nb_noeuds) if nb_noeuds > 0 else 0
            print(
                f"{semaine.strftime('%Y-%m-%d')} : {nb_noeuds} nœuds, "
                f"plus grosse composante = {plus_grosse} ({ratio}%)"
            )

        resultats.append({
            "semaine": semaine,
            "nb_composantes": nb_composantes,
            "nb_noeuds": nb_noeuds,
            "taille_composante_geante": plus_grosse,
            "ratio_composante_geante": (
                plus_grosse / nb_noeuds if nb_noeuds > 0 else 0
            ),
        })

    df_resultats = pd.DataFrame(resultats)

    if save:
        df_resultats.to_csv(output_csv, index=False)
        if verbose:
            print(f"Composantes connexes sauvegardées : {output_csv}")

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
    plt.title(f"Fragmentation du réseau maritime {year}")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    if save:
        plt.savefig(output_fig, dpi=300)
        if verbose:
            print(f"✓ Graphique composantes sauvegardé : {output_fig}")

    plt.show()

    return df_resultats


if __name__ == "__main__":
    for year in [2010, 2002]:
        calculer_densite_temporelle(year=year)
        analyser_composantes_connexes(year=year)