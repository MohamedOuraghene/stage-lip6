📂 1. Pathlib : La gestion propre des dossiers et fichiers
Fini l'époque des chaînes de caractères comme "C:/Users/..." qui font planter le code quand on passe d'un PC Windows (LIP6) à ton PC portable. pathlib manipule des objets chemins.

Les indispensables :
Path(__file__) : C'est le chemin absolu du fichier .py dans lequel tu écris cette ligne.

.resolve().parent : Remonte d'un niveau dans les dossiers.

Path(__file__).resolve().parent.parent permet de remonter à la racine de ton repo stage-lip6/ depuis le sous-dossier src/.

L'opérateur / : pathlib surcharge l'opérateur de division / pour fusionner des chemins proprement, peu importe le système d'exploitation.

racine / "data" / "fichier.csv" construira le bon chemin que tu sois sur Windows ou Linux.

.exists() : Renvoie un booléen (True/False). Idéal pour sécuriser ton pipeline (ex: vérifier si le fichier nettoyé existe avant de lancer le clustering).

.mkdir(parents=True, exist_ok=True) : Crée un dossier. exist_ok=True évite que Python ne lève une erreur si le dossier existe déjà.

🐼 2. Pandas : Le roi de la manipulation de tableaux
En Pandas, un tableau s'appelle un DataFrame (abrégé df), et une colonne unique est une Series.

Les masques booléens (Le filtrage)
Pour filtrer des lignes, on n'utilise jamais de boucles for. On crée un masque de conditions :

Python
# Crée une série de True/False de la même longueur que le tableau
masque = df["FREQUENTATION"] >= 100

# On passe le masque au DataFrame pour extraire les lignes correspondantes
hubs = df[masque]
Combiner les conditions : On utilise & (ET), | (OU), et ~ (NON/Inversion). Attention : il faut obligatoirement mettre des parenthèses autour de chaque condition.

Python
petits_ports_p = df[(df["Type"] == "P") & (df["FREQUENTATION"] < 100)]
Gérer les trous (NaN) : .isna() trouve les lignes vides, .notna() trouve les lignes remplies.

L'agrégation avec .groupby()
Le .groupby() découpe ton tableau en sous-groupes selon une ou plusieurs colonnes, puis applique une opération de calcul.

.size() : Compte le nombre de lignes par groupe (ce qui te donne ta fréquentation).

.reset_index(name="...") : Très important ! Après un groupby, Pandas transforme tes colonnes de groupe en "index". .reset_index() remet le tableau à plat sous forme de DataFrame standard et te permet de renommer la colonne de calcul.

Le croisement de fichiers avec .merge()
C'est l'équivalent d'un JOIN en SQL ou d'un RECHERCHEV en Excel.

Python
df_final = df_gauche.merge(df_droite, left_on="PLACE ID", right_on="ID_Lloyds", how="left")
how="left" : Signifie qu'on garde toutes les lignes de ton tableau de séjours (df_gauche), et qu'on vient y coller les infos géographiques du Excel s'il trouve une correspondance. Si le port n'est pas dans le Excel, les colonnes géographiques prendront la valeur NaN (mais on ne perd pas le séjour !).

🧮 3. NumPy & Vectorisation : La vitesse pure
En Python standard, faire des calculs mathématiques dans une boucle for sur 10 000 ou 65 000 lignes est extrêmement lent. NumPy permet de faire des calculs vectorisés.

Le concept de vectorisation
Au lieu de calculer la distance ligne par ligne, tu passes à une fonction NumPy deux tableaux entiers de coordonnées. NumPy effectue le calcul sur toutes les lignes simultanément en utilisant du code compilé en C (bas niveau) en arrière-plan. C'est ce qui fait passer un calcul de 5 minutes à 0,2 seconde.

Les outils indispensables pour ton algo :
np.radians(df["colonne"]) : Convertit un tableau entier de degrés en radians d'un seul coup (obligatoire pour les formules trigonométriques comme Haversine).

np.sin(), np.cos(), np.arcsin(), np.sqrt() : Les fonctions trigonométriques optimisées pour les tableaux.

np.argmin(tableau_distances) : Parcourt un tableau de distances et renvoie l'index (la position) de la valeur la plus petite. C'est l'outil parfait pour trouver "le port le plus proche".

🐍 4. Python : Portée et Sûreté
La Portée (Scope) : Une variable créée à l'intérieur d'une fonction (def) est locale. Elle meurt dès que la fonction se termine. Pour faire sortir une donnée d'une fonction, on utilise impérativement le mot-clé return.

if __name__ == "__main__": : Garantit que le code en dessous ne s'exécute que si tu lances ce fichier précis via ton terminal. Si un autre script importe ton fichier pour lui emprunter une fonction, ce code est ignoré.