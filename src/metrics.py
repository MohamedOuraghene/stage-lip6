import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt


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

    # Visualisation
    plt.figure(figsize=(14, 5))
    densite.plot()
    plt.xlabel("Date")
    plt.ylabel("Nombre de liens actifs δ(t)")
    plt.title("Densité temporelle du réseau maritime 2010")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

    return densite


if __name__ == "__main__":
    calculer_densite_temporelle()