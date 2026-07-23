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


def prepare_ports_for_clustering(rayon_km=44.0, pourcentage_seuil=0.001, save=True, verbose=True):
    base_dir = Path(__file__).resolve().parent.parent
    clean_csv_path = base_dir / "data_clean" / "stays_basic_info_2010_clean.csv"
    output_csv_path = base_dir / "data_clean" / "ports_clustered_2010.csv"
    
    if not clean_csv_path.exists():
        print(" fichier clean introuvable. lance d'abord clean.py ")
        return None

    # Charger le fichier CSV nettoyé
    df = pd.read_csv(clean_csv_path)

    # 1. Calculer la fréquentation par Port
    ports_stats = df.groupby(["PLACE ID", "Name_Final", "COUNTRY", "X1", "Y1", "Type"], dropna=False).size().reset_index(name="FREQUENTATION")
    
    # 2. paramétrage du seuil dynamique
    trafic_total = ports_stats["FREQUENTATION"].sum()
    SEUIL_DYNAMIQUE = int(trafic_total * pourcentage_seuil)

    if verbose:
        print("\n DIAGNOSTIC GLOBAL ")
        print(f" Trafic mondial total : {trafic_total} séjours.")
        print(f" Seuil dynamique : ≥ {SEUIL_DYNAMIQUE} séjours pour être un Hub.")
        print(" \n")

    # 3. calcul des distances aux ports P les plus proches
    # On commence par éliminer TOUS les points qui n'ont pas de coordonnées GPS valides (X1 ou Y1 est NaN)
    ports_stats_geo = ports_stats.dropna(subset=["X1", "Y1"])
    
    # On fait nos groupes sur ce tableau propre géographiquement
    ports_P = ports_stats_geo[ports_stats_geo["Type"] == "P"].copy()
    ports_autres = ports_stats_geo[ports_stats_geo["Type"] != "P"].copy()

    if ports_P.empty:
        print(" Erreur critique : Aucun port de Type P trouvé dans le dataset!.")
        return None

    # Pour chaque point secondaire, on cherche sa distance au port P le plus proche
    distances_minimales = []
    ids_port_proche = []
    noms_port_proche = []

    # Boucle sur les points secondaires
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
    ports_complet = pd.concat([ports_P, ports_autres]).sort_values(by="FREQUENTATION", ascending=False)

    # Stratégie de fusion des ports A et L avec les ports P proches
    RAYON_MAX_KM = rayon_km

    # Masque de trafic pour les ports commerciaux (P) et les zones A/L
    a_gros_trafic = ports_complet["FREQUENTATION"] >= SEUIL_DYNAMIQUE
    
    # Condition 1 : Les types qui sont TOUJOURS des hubs autonomes 
    est_hub_par_nature = ports_complet["Type"].isin(["T", "C", "W", "O"])
    
    # Condition 2 : Les ports commerciaux (P) assez gros pour être autonomes
    est_port_P_majeur = (ports_complet["Type"] == "P") & a_gros_trafic
    
    # Condition 3 : Les zones A et L isolées mais genr sauvées par leur gros trafic 
    est_A_ou_L = ports_complet["Type"].isin(["A", "L"])
    est_isole = ports_complet["DIST_PORT_PROCHE"] > RAYON_MAX_KM
    L_ou_A_hub_sauve = est_A_ou_L & est_isole & a_gros_trafic

    # GROUPE 1 : Les Hubs Finaux (Laissés 100% autonomes)
    Hubs_Finaux = ports_complet[est_hub_par_nature | est_port_P_majeur | L_ou_A_hub_sauve]

    # GROUPE 2 : Les Nœuds à agglomérer (Petits ports P, ou A/L proches)
    est_proche = ports_complet["DIST_PORT_PROCHE"] <= RAYON_MAX_KM
    A_ou_L_a_fusionner = est_A_ou_L & est_proche
    petits_ports_P = (ports_complet["Type"] == "P") & ~a_gros_trafic
    
    Agglomerations_Candidats = ports_complet[petits_ports_P | A_ou_L_a_fusionner]

    # GROUPE 3 : Le bruit éliminé (Uniquement les A ou L isolés à faible trafic)
    Bruit_Elimine = ports_complet[est_A_ou_L & est_isole & ~a_gros_trafic]

    # 5. AFFICHAGE DES RÉSULTATS DU TRI
    if verbose:
        print("     SÉPARATION FINALE ")
        print(f" HUBS FINAUX AUTONOMES : {len(Hubs_Finaux)} points.")
        print(f" POINTS À AGGLOMÉRER GÉOGRAPHIQUEMENT : {len(Agglomerations_Candidats)} points.")
        print(f" NOEUDS ÉLIMINÉS (Bruit de fond) : {len(Bruit_Elimine)} points.")
        print("\n")

    # Étape 1 : Initialisation des clusters par défaut
    ports_complet["Cluster_ID"] = ports_complet["PLACE ID"]
    ports_complet["Cluster_Name"] = ports_complet["Name_Final"]

    # Étape 2 : Isoler les ports de type P pour appliquer Clustering 
    ports_P_uniquement = ports_complet[ports_complet["Type"] == "P"].copy()

    # On récupère les coordonnées GPS
    lons = ports_P_uniquement["X1"].values
    lats = ports_P_uniquement["Y1"].values

    # Calcul de la matrice de distances
    matrice_distances = haversine_vectorized(lons[:, np.newaxis], lats[:, np.newaxis], lons[np.newaxis, :], lats[np.newaxis, :])

    # Compression de la matrice pour SciPy
    vecteur_distances = squareform(matrice_distances, checks=False)

    # Construction de l'arbre (Linkage)
    arbre_clustering = linkage(vecteur_distances, method="average")

    # Coupe de l'arbre au rayon choisi (Fcluster)
    labels_clusters = fcluster(arbre_clustering, t=RAYON_MAX_KM, criterion="distance")

    # On ajoute ces numéros de clusters temporaires
    ports_P_uniquement["SciPy_Cluster_ID"] = labels_clusters

    # Tri par fréquentation décroissante : le "chef" de chaque cluster sera en première position
    ports_P_uniquement = ports_P_uniquement.sort_values(by="FREQUENTATION", ascending=False)

    # Propagation via .transform("first")
    ports_P_uniquement["Cluster_ID_Definitif"] = (
        ports_P_uniquement.groupby("SciPy_Cluster_ID")["PLACE ID"].transform("first")
    )

    ports_P_uniquement["Cluster_Name_Definitif"] = (
        ports_P_uniquement.groupby("SciPy_Cluster_ID")["Name_Final"].transform("first")
    )

    # Etape 3 : Jointure finale 
    table_correspondance = ports_P_uniquement[["PLACE ID", "Cluster_ID_Definitif", "Cluster_Name_Definitif"]]

    ports_complet = ports_complet.merge(
        table_correspondance,
        left_on="PORT_PROCHE_ID",
        right_on="PLACE ID",
        how="left",
        suffixes=("", "_y")
    )

    # Attribution de l'ID de cluster et du nom harmonisé 
    ports_complet["Cluster_ID"] = ports_complet["Cluster_ID_Definitif"].fillna(ports_complet["PLACE ID"])
    ports_complet["Cluster_Name"] = ports_complet["Cluster_Name_Definitif"].fillna(ports_complet["Name_Final"])

    # Ajout propre du suffixe " Area" pour tout le monde
    ports_complet["Cluster_Name"] = ports_complet["Cluster_Name"].astype(str) + " Area"

    # Nettoyage des colonnes temporaires
    ports_complet = ports_complet.drop(columns=["Cluster_ID_Definitif", "Cluster_Name_Definitif", "PLACE ID_y"])

    #frequentation_sorted = ports_stats["FREQUENTATION"].sort_values(ascending=False)
    #plt.plot(range(1, len(frequentation_sorted)+1), frequentation_sorted.values)
    #plt.xlabel("Rang du port (log)")
    #plt.ylabel("Fréquentation (log)")
    #plt.title("Distribution de la fréquentation des ports (échelle log-log)")
    #plt.show()"

    # sauvegarde du fichier pour étapes suivantes
    if save:
        ports_complet.to_csv(output_csv_path, index=False)
        if verbose:
            print(f" Fichier de clustering sauvegardé dans : {output_csv_path}")

    return ports_complet


def tester_combinaison(rayon_km, pourcentage_seuil):
    """Lance le clustering avec un couple (rayon, seuil) et renvoie nb_clusters + taux de réduction."""
    ports_complet = prepare_ports_for_clustering(
        rayon_km=rayon_km,
        pourcentage_seuil=pourcentage_seuil,
        save=False,
        verbose=False,
    )
    if ports_complet is None:
        return None, None

    nb_initiaux = ports_complet["PLACE ID"].nunique()
    nb_clusters = ports_complet["Cluster_ID"].nunique()
    taux_reduction = (nb_initiaux - nb_clusters) / nb_initiaux * 100
    return nb_clusters, taux_reduction


if __name__ == "__main__":
    # 1. On lance le clustering et on récupère le tableau final
    ports_final = prepare_ports_for_clustering()
    
    if ports_final is not None:
        # 2. On compte les points uniques de départ et les clusters d'arrivée
        nb_points_initiaux = ports_final["PLACE ID"].nunique()
        nb_clusters_finaux = ports_final["Cluster_ID"].nunique()
        taux_reduction = (nb_points_initiaux - nb_clusters_finaux) / nb_points_initiaux * 100

        # 3. Affichage du résultat
        print("\n      TEST DE COMPLEXITÉ ")
        print(f"• Nombre de points au départ (brut) : {nb_points_initiaux}")
        print(f"• Nombre de zones à l'arrivée (clusters) : {nb_clusters_finaux}")
        print(f"➔ RÉDUCTION DE LA COMPLEXITÉ : {taux_reduction:.1f}%")
        print(" \n")

    # 4. Matrice de sensibilité (grid search simple)
    rayons_to_test = [30, 44, 75, 100, 150]
    seuils_to_test = [0.001, 0.005, 0.01, 0.02]

    resultats = []
    for r in rayons_to_test:
        for s in seuils_to_test:
            nb_c, taux = tester_combinaison(rayon_km=r, pourcentage_seuil=s)
            resultats.append({
                "Rayon (km)": r,
                "Seuil Trafic (%)": s * 100,
                "Nb Clusters": nb_c,
                "Reduction (%)": round(taux, 1) if taux is not None else None,
            })

    df_res = pd.DataFrame(resultats)
    print("\n================ MATRICE DE SENSIBILITE ================")
    print(df_res.to_string(index=False))
    print()