import pandas as pd
from pathlib import Path

def prepare_ports_for_clustering():
    base_dir = Path(__file__).resolve().parent.parent
    clean_csv_path = base_dir / "data_clean" / "stays_basic_info_2010_clean.csv"
    
    if not clean_csv_path.exists():
        print("❌ Fichier clean introuvable.Il faut Lancer d'abord clean.py !")
        return

    # Charger les données nettoyées
    df = pd.read_csv(clean_csv_path)

    # 1. Calculer la fréquentation par Port
    # On regroupe par les caractéristiques uniques du port pour ne pas perdre ses coordonnées GPS
    ports_stats = df.groupby(["PLACE ID", "Name_Final", "COUNTRY", "X1", "Y1","Type"], dropna=False).size().reset_index(name="FREQUENTATION")
    
    # Trier par plus fréquenté
    ports_stats = ports_stats.sort_values(by="FREQUENTATION", ascending=False)

    print(f"✓ Nombre total de ports uniques trouvés : {len(ports_stats)}")
    
    # 2. Séparer les "HubsMajeurs" (Zones autonomes) des petits ports
    SEUIL = 100
    HubsMajeurs = ports_stats[ports_stats["FREQUENTATION"] >= SEUIL]
    petits_ports = ports_stats[ports_stats["FREQUENTATION"] < SEUIL]

    print(f"✓ Ports 'HubsMajeurs' (≥ {SEUIL} trajets, laissés autonomes) : {len(HubsMajeurs)}")
    print(f"✓ Petits ports à agglomérer : {len(petits_ports)}")
    
    print("\nAperçu des ports HubsMajeurs :")
    print(HubsMajeurs.head(20))

    return HubsMajeurs, petits_ports

if __name__ == "__main__":
    prepare_ports_for_clustering()

    

  