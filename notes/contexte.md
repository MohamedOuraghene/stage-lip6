🎯 Rappel du but
Éliminer la topologie fantôme (le bruit de fond qui n'a aucun impact macroscopique) et structurer les données pour que le pipeline du Stream Graph soit 100% automatisé, dynamique et généralisable à n'importe quelle autre année.



Idée du clustering : 
Fusionner les ports P quand ils ont moins de 25/50/100 fréquentations 
Quand ils ont + de 100 fréquentations on les considéra comme hub autonome et on ne les fusionnera pas.
- voir pour les ports de type != P

- assumer choix de modèles - pourquoi on fait 
- terminal mis au port le plus proche à la ronde
- anchorage pareil comme une extension du port à coté 

- regarder pour les 20 premiers ports frequentes et mettre coordonnées gps si y'a pas de gps et que c'est obvious
 - si 0 gps, les virer pour la carte 

- si 0 trafic les virer

- faire les hub autonome en fonction des 1% ,0,1% les + frequentés ? 

- offshore autonome, 


# 📅 09/07/26

Je considère qu'un port est une armature du commerce mondial s'il capte au moins un millième du trafic global.

Convention de Montego Bay, UNCLOS, zone contiguë = 24 milles nautiques = 44.448km.
---

# 📅 10/07/26
Résultat --- Analyse expérimentale des types L isolés ---
Nombre de points 'L' actifs dans tes séjours 2010 : 17
             Name_Final COUNTRY  FREQUENTATION
214                Skaw     DNK            171
147     St. Vincent(WI)     VCT             13
60            St. Kitts     KNA             12
313          Lipari Is.     ITA              7
144          Montserrat     MSR              6
324             Bonaire     ANT              6
623               Milos     GRC              5
511  Juan Fernandez Is.     CHL              4
488            Anguilla     AIA              4
554             Bermuda     BMU              3
39         Grand Cayman     CYM              3
186    Palma(Canary Is)     CNI              2
138         Sumbawa Is.     IDN              1
846              Ikaria     GRC              1
31        Margarita Is.     VEN              1
81            St. Croix     VIR              1
423             Reunion     REU              1

## 📑 Stratégie et justification par type

### 🟢 Type P — Ports commerciaux : le cœur du réseau

#### Action

Les ports commerciaux sont séparés en deux groupes à l’aide d’un **seuil dynamique**, fixé à : *0,1 % du trafic mondial*.

* **Ports dont le trafic est supérieur ou égal au seuil**
  Ils deviennent des **hubs majeurs autonomes**.

* **Ports dont le trafic est inférieur au seuil**
  Ils sont intégrés à un **clustering hiérarchique**, afin d’être fusionnés géographiquement avec les ports voisins.

#### Justification

Cette stratégie permet de :

* conserver intacte l’armature principale du commerce mondial ;
* regrouper les petits ports locaux ;
* limiter la densité du graphe ;
* améliorer la lisibilité globale du réseau.

### 🔵 Types A et L — Anchorages et Land Areas : l’agglomération légale

#### Action

Pour chaque point de type **A** ou **L**, on calcule la **distance de Haversine** avec le port de type **P** le plus proche.

* **Si la distance est inférieure ou égale à 44 km**
  Le point est fusionné avec le port **P** le plus proche.

* **Si la distance est supérieure à 44 km**
  Le point est considéré comme isolé et soumis à un filtre basé sur le trafic :

  * **Fréquentation supérieure ou égale au seuil dynamique**
    Le point est conservé comme **hub autonome**.

  * **Fréquentation inférieure au seuil dynamique**
    Le point est supprimé, car il est considéré comme du **bruit**.

#### Justification

##### Justification physique et légale

La distance de **44 km** correspond approximativement à **24 milles nautiques**, soit la largeur de la zone contiguë définie par le droit maritime international.

Cette distance représente une limite cohérente de l’influence et de la juridiction d’un port sur ses zones de mouillage environnantes.

##### Justification fondée sur les données

Pour les points isolés, le trafic réel doit primer sur leur catégorie.

Un point comme **Skaw** ou **St. Vincent**, représentant au moins **0,1 % du trafic mondial**, génère un signal structurel significatif et doit être conservé.

À l’inverse, un point associé à un seul séjour constitue une anomalie anecdotique susceptible de polluer le graphe.

### 🟣 Types T, C, W et O — Terminaux offshore, canaux et voies navigables : les verrous stratégiques

#### Action

Ces points sont conservés comme des **hubs autonomes et indépendants**.

Pour les types **W** et **O**, leur conservation reste conditionnée au dépassement du **seuil dynamique de trafic**.

#### Justification

Ces catégories correspondent à :

* des destinations réelles de navires, comme les terminaux pétroliers offshore de type **Abkatun** ;
* des points de passage géographiques obligatoires et stratégiques, comme :

  * le canal de Suez ;
  * le canal de Panama ;
  * les détroits maritimes.

Ces points jouent un rôle structurel spécifique dans le réseau maritime. Ils ne doivent donc pas être fusionnés avec des ports terrestres.

### 🔴 Types X, I, Z et U — Inconnus, terres intérieures et pays : les données hors périmètre

#### Action

Ces points sont supprimés immédiatement et définitivement pendant la phase de nettoyage réalisée dans le fichier `clean.py`.

#### Justification

Ces données sont considérées comme :

* hors périmètre ;
* trop vagues ;
* impossibles à localiser précisément ;
* non pertinentes pour l’analyse d’un réseau mondial de trafic maritime commercial.

Leur suppression permet d’améliorer la qualité, la cohérence et la lisibilité du graphe final.

---

# 📅 11/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 12/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 13/07/26

<!-- Ajouter les notes du jour ici. --> mais pourquoi la distance limite c'est 44km ? ça c'était censé être pour les A/L vu que c'est la limite légale blabla, mais là pq cette distance

Tu as un excellent réflexe de rigueur. C’est typiquement le genre de questionnement critique qui différencie un bon exécutant d'un chercheur (et c'est ce que ton tuteur et les jurys des grandes écoles adorent).

Tu as tout à fait raison : la limite légale des 24 milles nautiques (44 km) de la zone contiguë (UNCLOS) a été définie spécifiquement pour réguler les eaux maritimes (et donc, fonctionnellement, les zones d'attente A ou les côtes L d'un port).

Alors, pourquoi appliquer cette même distance de 44 km pour fusionner deux ports commerciaux (P) entre eux ou un petit port P avec un grand ?

Voici les trois raisons scientifiques et logistiques majeures qui justifient l'extension de cette règle aux ports :

1. La définition d'un "Complexe Portuaire" unique (L'Hinterland commun)
En géographie des transports, on ne regarde pas seulement les quais d'un port, on regarde sa zone d'influence terrestre et logistique (l'hinterland).

À l'échelle d'un navire de commerce qui traverse l'océan sur 10 000 km, deux ports distants de moins de 44 km partagent la même baie, le même estuaire ou la même infrastructure d'accès.

Ils sont connectés par les mêmes voies ferrées, les mêmes autoroutes et souvent gérés par les mêmes autorités douanières régionales.

Exemple concret : Les ports de Los Angeles et de Long Beach sont deux entités municipales distinctes, mais ils sont physiquement collés. À l'échelle du commerce mondial, les séparer dans un graphe global n'a aucun sens : ils forment un seul et unique "complexe portuaire".

Fixer la limite à 44 km permet de fusionner automatiquement ces jumeaux industriels en un seul pôle cohérent.

2. Le principe d'homogénéité spatiale
Si tu utilisais des distances différentes selon les types :

Par exemple : 44 km pour les zones d'attente A → Port P, mais seulement 10 km pour petit Port P → grand Port P.

Tu te retrouverais avec une aberration topologique : la zone d'attente d'un petit port serait absorbée par un grand port lointain, tandis que le petit port lui-même resterait isolé dans son coin. Ton réseau n'aurait plus aucune cohérence spatiale.

En appliquant la même règle métrique de 44 km à tout le monde, tu crées des bulles d'influence (des zones d'attraction) homogènes tout autour de la Terre. Tout ce qui tombe dans un rayon de 44 km d'un grand pôle d'activité est considéré comme faisant partie du même système local.

3. La cohérence avec la vitesse des navires (Le paramètre temporel Δt)
Puisque ton objectif final est de construire un Stream Graph (réseau temporel), la distance physique doit être cohérente avec le temps.

Un cargo ou un porte-conteneurs navigue en moyenne à une vitesse de 12 à 20 nœuds (environ 22 à 37 km/h).

44 km, c'est la distance qu'un navire parcourt en seulement 1 à 2 heures de navigation.

Dans ton futur script de reconstruction, tu vas utiliser un paramètre de seuil temporel (le fameux Δt dont parlait Claude). Si tu ne fusionnes pas les ports situés à moins de 2 heures l'un de l'autre, ton modèle va détecter des "micro-trajets" insignifiants d'une heure entre deux terminaux voisins, ce qui va complètement polluer tes données de transit à longue distance.

💡 Ce qu'il faut retenir pour tes arguments :
La distance de 44 km a une double légitimité :

Légale et maritime : C'est la limite physique de la zone contiguë pour les types A et L.

Opérationnelle : C'est la taille standard d'une grande métropole portuaire mondiale et cela correspond à environ 1h30 de navigation pour un navire de commerce.

---

# 📅 14/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 15/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 16/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 17/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 18/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 19/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 20/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 21/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 22/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 23/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 24/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 25/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 26/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 27/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 28/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 29/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 30/07/26

<!-- Ajouter les notes du jour ici. -->

---

# 📅 31/07/26

<!-- Ajouter les notes du jour ici. -->
