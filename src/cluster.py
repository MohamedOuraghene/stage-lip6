import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def haversine_vectorized(lon1, lat1, lon2, lat2):
    """
    Calcule la distance en kilomètres entre deux points ou deux séries de points GPS.
    Prend en entrée des degrés décimaux.
    """
    # Conversion des degrés en radians
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    
    # Formule de Haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2.0 * np.arcsin(np.sqrt(a))
    
    # Rayon de la Terre en kilomètres
    rayon_terre = 6371.0
    return c * rayon_terre


def prepare_ports_for_clustering():
    base_dir = Path(__file__).resolve().parent.parent
    clean_csv_path = base_dir / "data_clean" / "stays_basic_info_2010_clean.csv"
    
    if not clean_csv_path.exists():
        print("❌ Fichier clean introuvable. Il faut lancer d'abord clean.py !")
        return

    # Charger le fichier CSV nettoyé
    df = pd.read_csv(clean_csv_path)

    # 1. Calculer la fréquentation par Port
    ports_stats = df.groupby(["PLACE ID", "Name_Final", "COUNTRY", "X1", "Y1", "Type"], dropna=False).size().reset_index(name="FREQUENTATION")
    
    # 2. Paramétrage du seuil dynamique
    trafic_total = ports_stats["FREQUENTATION"].sum()
    pourcentage_seuil = 0.001 
    SEUIL_DYNAMIQUE = int(trafic_total * pourcentage_seuil)

    print("\n================ DIAGNOSTIC GLOBAL ================")
    print(f"✓ Trafic mondial total : {trafic_total} séjours.")
    print(f"✓ Seuil dynamique (0.1%) : ≥ {SEUIL_DYNAMIQUE} séjours pour être un Hub.")
    print("===================================================\n")

    # 3. CALCUL DYNAMIQUE DES DISTANCES AU PORT 'P' LE PLUS PROCHE
    # On commence par éliminer TOUS les points qui n'ont pas de coordonnées GPS valides (X1 ou Y1 est NaN)
    ports_stats_geo = ports_stats.dropna(subset=["X1", "Y1"])
    
    # On fait nos groupes sur ce tableau propre géographiquement
    ports_P = ports_stats_geo[ports_stats_geo["Type"] == "P"].copy()
    ports_autres = ports_stats_geo[ports_stats_geo["Type"] != "P"].copy()

    if ports_P.empty:
        print("❌ Erreur critique : Aucun port de Type 'P' trouvé dans le dataset.")
        return

    # Pour chaque point secondaire, on cherche sa distance au port P le plus proche
    distances_minimales = []
    ids_port_proche = []
    noms_port_proche = []

    # Boucle optimisée sur les points secondaires (il y en a très peu)
    for idx, row in ports_autres.iterrows():
        # Calcul de la distance entre CE point secondaire et TOUS les ports P du monde
        distances = haversine_vectorized(row["X1"], row["Y1"], ports_P["X1"], ports_P["Y1"])
        
        # On trouve l'index du port P le plus proche
        idx_proche = distances.idxmin()
        
        # On extrait la distance minimale et les infos du port associé
        distances_minimales.append(distances.min())
        ids_port_proche.append(ports_P.loc[idx_proche, "PLACE ID"])
        noms_port_proche.append(ports_P.loc[idx_proche, "Name_Final"])

    # On ajoute ces nouvelles colonnes à notre tableau de points secondaires
    ports_autres["DIST_PORT_PROCHE"] = distances_minimales
    ports_autres["PORT_PROCHE_ID"] = ids_port_proche
    ports_autres["PORT_PROCHE_NAME"] = noms_port_proche

    # Les ports de type P ont une distance de 0 par rapport à eux-mêmes
    ports_P["DIST_PORT_PROCHE"] = 0.0
    ports_P["PORT_PROCHE_ID"] = ports_P["PLACE ID"]
    ports_P["PORT_PROCHE_NAME"] = ports_P["Name_Final"]

    # On rassemble tout le monde dans un seul grand tableau propre
    ports_complet = pd.concat([ports_P, ports_output_provisoire := ports_autres]).sort_values(by="FREQUENTATION", ascending=False)

    # 4. APPLICATION DE TA STRATÉGIE SCIENTIFIQUE (Les Masques Booléens)
    RAYON_MAX_KM = 44.0

    # Masque de trafic pour les ports commerciaux (P) et les zones A/L
    a_gros_trafic = ports_complet["FREQUENTATION"] >= SEUIL_DYNAMIQUE
    
    # Condition 1 : Les types qui sont TOUJOURS des hubs autonomes (Ta décision)
    est_hub_par_nature = ports_complet["Type"].isin(["T", "C", "W", "O"])
    
    # Condition 2 : Les ports commerciaux (P) assez gros pour être autonomes
    est_port_P_majeur = (ports_complet["Type"] == "P") & a_gros_trafic
    
    # Condition 3 : Les zones A et L isolées sauvées par leur gros trafic (ex: Skaw)
    est_A_ou_L = ports_complet["Type"].isin(["A", "L"])
    est_isole = ports_complet["DIST_PORT_PROCHE"] > RAYON_MAX_KM
    L_ou_A_hub_sauve = est_A_ou_L & est_isole & a_gros_trafic

    # GROUPE 1 : Les Hubs Finaux (Laissés 100% autonomes dans le Stream Graph)
    Hubs_Finaux = ports_complet[est_hub_par_nature | est_port_P_majeur | L_ou_A_hub_sauve]

    # GROUPE 2 : Les Nœuds à agglomérer (Petits ports P, ou A/L proches < 44km)
    est_proche = ports_complet["DIST_PORT_PROCHE"] <= RAYON_MAX_KM
    A_ou_L_a_fusionner = est_A_ou_L & est_proche
    petits_ports_P = (ports_complet["Type"] == "P") & ~a_gros_trafic
    
    Agglomerations_Candidats = ports_complet[petits_ports_P | A_ou_L_a_fusionner]

    # GROUPE 3 : Le bruit éliminé (Uniquement les A ou L isolés à faible trafic)
    Bruit_Elimine = ports_complet[est_A_ou_L & est_isole & ~a_gros_trafic]

    # 5. AFFICHAGE DES RÉSULTATS DU TRI
    print("================ SÉPARATION FINALE ================")
    print(f" HUBS FINAUX AUTONOMES : {len(Hubs_Finaux)} points.")
    print(f" POINTS À AGGLOMÉRER GÉOGRAPHIQUEMENT : {len(Agglomerations_Candidats)} points.")
    print(f" NOEUDS ÉLIMINÉS (Bruit de fond) : {len(Bruit_Elimine)} points.")
    print("===================================================\n")



    #frequentation_sorted = ports_stats["FREQUENTATION"].sort_values(ascending=False)
    #plt.plot(range(1, len(frequentation_sorted)+1), frequentation_sorted.values)
    #plt.xlabel("Rang du port (log)")
    #plt.ylabel("Fréquentation (log)")
    #plt.title("Distribution de la fréquentation des ports (échelle log-log)")
    #plt.show()

    if not Bruit_Elimine.empty:
        print("Aperçu du bruit éliminé (Vérification de sûreté) :")
        print(Bruit_Elimine[["Name_Final", "Type", "FREQUENTATION", "DIST_PORT_PROCHE"]].head(10))

    return Hubs_Finaux, Agglomerations_Candidats

if __name__ == "__main__":
    prepare_ports_for_clustering()