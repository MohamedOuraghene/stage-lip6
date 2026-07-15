import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform


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
        print(" Fichier clean introuvable.  lancer d'abord clean.py !")
        return

    # charger le fichier CSV nettoyé
    df = pd.read_csv(clean_csv_path)

    # 1. Calculer la fréquentation par Port
    ports_stats = df.groupby(["PLACE ID", "Name_Final", "COUNTRY", "X1", "Y1", "Type"], dropna=False).size().reset_index(name="FREQUENTATION")
    
    # 2. Paramétrage du seuil dynamique
    trafic_total = ports_stats["FREQUENTATION"].sum()
    pourcentage_seuil = 0.001 
    SEUIL_DYNAMIQUE = int(trafic_total * pourcentage_seuil)

    print("\n================ DIAGNOSTIC GLOBAL ================")
    print(f" Trafic mondial total : {trafic_total} séjours.")
    print(f" Seuil dynamique (0.1%) : ≥ {SEUIL_DYNAMIQUE} séjours pour être un Hub.")
    print("===================================================\n")

    # 3. CALCUL DYNAMIQUE DES DISTANCES AU PORT 'P' LE PLUS PROCHE
    # On commence par éliminer TOUS les points qui n'ont pas de coordonnées GPS valides (X1 ou Y1 est NaN)
    ports_stats_geo = ports_stats.dropna(subset=["X1", "Y1"])
    
    # On fait nos groupes sur ce tableau propre géographiquement
    ports_P = ports_stats_geo[ports_stats_geo["Type"] == "P"].copy()
    ports_autres = ports_stats_geo[ports_stats_geo["Type"] != "P"].copy()

    if ports_P.empty:
        print(" Erreur critique : Aucun port de Type P trouvé dans le dataset!.")
        return

    # Pour chaque point secondaire, on cherche sa distance au port P le plus proche
    distances_minimales = []
    ids_port_proche = []
    noms_port_proche = []

    # boucle  sur les points secondaires
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

    # stratégie de fusion des ports A et L avec les ports P proches
    RAYON_MAX_KM = 44.0

    # Masque de trafic pour les ports commerciaux (P) et les zones A/L
    a_gros_trafic = ports_complet["FREQUENTATION"] >= SEUIL_DYNAMIQUE
    
    # Condition 1 : Les types qui sont TOUJOURS des hubs autonomes 
    est_hub_par_nature = ports_complet["Type"].isin(["T", "C", "W", "O"])
    
    # Condition 2 : Les ports commerciaux (P) assez gros pour être autonomes
    est_port_P_majeur = (ports_complet["Type"] == "P") & a_gros_trafic
    
    # Condition 3 : Les zones A et L isolées sauvées par leur gros trafic (ex: Skaw)
    est_A_ou_L = ports_complet["Type"].isin(["A", "L"])
    est_isole = ports_complet["DIST_PORT_PROCHE"] > RAYON_MAX_KM
    L_ou_A_hub_sauve = est_A_ou_L & est_isole & a_gros_trafic

    # GROUPE 1 : Les Hubs Finaux (Laissés 100% autonomes)
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

    # étape 1 : initalisation des clusters avec chaque point comme son propre cluster

    ports_complet["Cluster_ID"] = ports_complet["PLACE ID"]
    ports_complet["Cluster_Name"] = ports_complet["Name_Final"]

    # étape 2 : création d'un masque pour la fusion des clusters pour les A et L proches d'un port P
    masque_A_L_proches = (
        ports_complet["Type"].isin(["A", "L"]) &
        (ports_complet["DIST_PORT_PROCHE"] <= RAYON_MAX_KM)
    )

    # Pour ces lignes-là, on remplace le Cluster_ID par l'ID du port P le plus proche
    ports_complet.loc[masque_A_L_proches, "Cluster_ID"] = ports_complet.loc[masque_A_L_proches, "PORT_PROCHE_ID"]
    ports_complet.loc[masque_A_L_proches, "Cluster_Name"] = ports_complet.loc[masque_A_L_proches, "PORT_PROCHE_NAME"]


    # étape 2.1 : ISOLER LES PORTS DE TYPE P 
    ports_P_uniquement = ports_complet[ports_complet["Type"] == "P"].copy() # application d'un masque pour garder que les type P et création d'un dataframe séparé

    #
    # on récupère les coordonnées gps en les mettant dans des arrays numpy pour pouvoir faire des calculs vectorisés
    lons = ports_P_uniquement["X1"].values
    lats = ports_P_uniquement["Y1"].values


    #étape 2.2 :  Calcul de la matrice de distances 
    matrice_distances = haversine_vectorized(lons[:, np.newaxis], lats[:, np.newaxis], lons[np.newaxis, :], lats[np.newaxis, :])

    # étape 2.3 : COMPRESSION DE LA MATRICE POUR SCIPY
    # SciPy n'aime pas les matrices carrées NxN redondantes (à cause de la symétrie).
    # 'squareform' la compresse en un vecteur plat 1D contenant uniquement la moitié utile.
    vecteur_distances = squareform(matrice_distances, checks=False)

    # étape 2.4 : CONSTRUCTION DE L'ARBRE (LINKAGE)
    # On utilise la méthode 'average' (liaison moyenne) : la distance entre deux clusters
    # est la moyenne des distances entre leurs ports. C'est la plus stable géographiquement.
    arbre_clustering = linkage(vecteur_distances, method="average")

    # étape 2.5 : COUPE DE L'ARBRE À 44 KM (FCLUSTER)
    # 't=RAYON_MAX_KM' : notre seuil de 44.0 km.
    # Cela renvoie un tableau d'identifiants de clusters (des entiers : 1, 2, 3...) de taille N.
    labels_clusters = fcluster(arbre_clustering, t=RAYON_MAX_KM, criterion="distance")

    # On ajoute ces numéros de clusters temporaires dans notre DataFrame des ports P
    ports_P_uniquement["SciPy_Cluster_ID"] = labels_clusters

        # 1. On trie par fréquentation décroissante : le "chef" de chaque cluster sera en première position
    ports_P_uniquement = ports_P_uniquement.sort_values(by="FREQUENTATION", ascending=False)

    # 2. On propage l'ID et le Nom du premier de chaque groupe à tout le groupe
    ports_P_uniquement["Cluster_ID_Definitif"] = (
        ports_P_uniquement.groupby("SciPy_Cluster_ID")["PLACE ID"].transform("first")
    )

    ports_P_uniquement["Cluster_Name_Definitif"] = (
        ports_P_uniquement.groupby("SciPy_Cluster_ID")["Name_Final"].transform("first") + " Area"
    )

    # Etape 3 : Jointure finale 
    
    # 1. On isole la table de correspondance directement depuis nos ports P
    table_correspondance = ports_P_uniquement[["PLACE ID", "Cluster_ID_Definitif", "Cluster_Name_Definitif"]]

    # 2. On fusionne cette table avec notre tableau complet 
    # (On joint sur le port de rattachement 'PORT_PROCHE_ID')
    ports_complet = ports_complet.merge(
        table_correspondance,
        left_on="PORT_PROCHE_ID",
        right_on="PLACE ID",
        how="left",
        suffixes=("", "_y")
    )

    # 3. Pour les types autonomes (T, C, W, O) qui n'ont pas de port proche, 
    # on garde leur propre ID et Nom d'origine (grâce à .fillna)
    ports_complet["Cluster_ID"] = ports_complet["Cluster_ID_Definitif"].fillna(ports_complet["PLACE ID"])
    ports_complet["Cluster_Name"] = ports_complet["Cluster_Name_Definitif"].fillna(ports_complet["Name_Final"])

    # On nettoie les colonnes temporaires créées par le merge
    ports_complet = ports_complet.drop(columns=["Cluster_ID_Definitif", "Cluster_Name_Definitif", "PLACE ID_y"])


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
    # 1. On lance le clustering et on récupère le tableau final
    ports_final = prepare_ports_for_clustering()
    
    if ports_final is not None:
        # 2. On compte les points uniques de départ et les clusters d'arrivée
        nb_points_initiaux = ports_final["PLACE ID"].nunique()
        nb_clusters_finaux = ports_final["Cluster_ID"].nunique()
        taux_reduction = (nb_points_initiaux - nb_clusters_finaux) / nb_points_initiaux * 100

        # 3. Affichage du résultat
        print("\n================ TEST DE COMPLEXITÉ ================")
        print(f"• Nombre de points au départ (brut) : {nb_points_initiaux}")
        print(f"• Nombre de zones à l'arrivée (clusters) : {nb_clusters_finaux}")
        print(f"➔ RÉDUCTION DE LA COMPLEXITÉ : {taux_reduction:.1f}%")
        print("====================================================\n")