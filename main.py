import argparse
import time
from pathlib import Path

from src.clean import clean_data
from src.cluster import prepare_ports_for_clustering
from src.analyse_greve_2002 import comparer
from src.metrics import analyser_composantes_connexes, calculer_densite_temporelle
from src.reconstruct import reconstruct_stream_graph


def run_pipeline(year, step, delta_t):
    start_time = time.time()
    print(f"\n🚀 [PIPELINE] Démarrage de l'exécution — Année : {year}")

    if step in ["clean", "all"]:
        print("\n--- 1. Nettoyage des données (clean) ---")
        clean_data(year=year)

    if step in ["cluster", "all"]:
        print("\n--- 2. Clustering Spatial UNCLOS (cluster) ---")
        prepare_ports_for_clustering(year=year)

    if step in ["reconstruct", "all"]:
        print(f"\n--- 3. Reconstruction Stream Graph (Δt = {delta_t}d) ---")
        reconstruct_stream_graph(year=year, delta_t=delta_t)

    if step in ["metrics", "all"]:
        print("\n--- 4. Calcul des Métriques Réseau (metrics) ---")
        calculer_densite_temporelle(year=year)
        analyser_composantes_connexes(year=year)

    if step in ["impact", "all"]:
        print("\n--- 5. Analyse Causale & Groupe Témoin (impact) ---")
        comparer(annee=year)

    duration = time.time() - start_time
    print(
        f"\n✅ [OK] Pipeline exécuté avec succès en {duration:.2f} secondes."
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Pipeline E2E d'analyse de résilience du trafic maritime mondial"
            " (LIP6)"
        )
    )

    parser.add_argument(
        "--year",
        type=int,
        choices=[2002, 2010],
        default=2002,
        help="Année du jeu de données à traiter (default: 2002)",
    )

    parser.add_argument(
        "--step",
        type=str,
        choices=[
            "clean",
            "cluster",
            "reconstruct",
            "metrics",
            "impact",
            "all",
        ],
        default="all",
        help="Étape spécifique du pipeline à exécuter (default: all)",
    )

    parser.add_argument(
        "--delta-t",
        type=int,
        default=30,
        help="Seuil de transit maximal en jours pour Δt (default: 30)",
    )

    args = parser.parse_args()
    run_pipeline(year=args.year, step=args.step, delta_t=args.delta_t)


if __name__ == "__main__":
    main()