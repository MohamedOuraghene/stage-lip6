# stage-lip6

Projet de stage au LIP6 — analyse et clustering de ports maritimes à partir de données de séjours de navires (2010).

## Objectif

Construire un pipeline pour :

1. **Nettoyer** les données de séjours et les enrichir avec les informations géographiques des ports
2. **Identifier** les hubs majeurs (ports très fréquentés, laissés autonomes)
3. **Fusionner** les petits ports avec le port ou hub le plus proche (en cours)

L'idée métier : les ports avec peu de fréquentation sont rattachés au port le plus proche ; ceux au-dessus d'un seuil (100 séjours pour l'instant) restent des hubs autonomes. Les terminaux (`T`) et mouillages (`A`) sont traités comme des extensions du port voisin.

## Structure du projet

```
stage-lip6/
├── data/                          # Données brutes (non versionnées)
│   ├── stays_basic_info_2010.csv
│   └── Matching_ports_city1_city2.xlsx
├── data_clean/                    # Données nettoyées (générées)
├── src/
│   ├── clean.py                   # Nettoyage et jointure avec le dictionnaire des ports
│   ├── cluster.py                 # Fréquentation et séparation hubs / petits ports
│   └── exploration_test.py        # Exploration des distances géographiques
└── notes/
    ├── contexte.md                # Idées et choix métier
    ├── guide.md                   # Aide-mémoire technique (pandas, pathlib, numpy)
    └── technique.md
```

## Prérequis

- Python 3.10+
- Les fichiers de données placés dans `data/` (voir ci-dessus)

## Installation

```powershell
# Créer l'environnement virtuel
python -m venv .venv

# Activer le venv (PowerShell)
.venv\Scripts\activate

# Si PowerShell bloque l'activation des scripts :
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Installer les dépendances
python -m pip install -r requirements.txt
```

Dépendances : `pandas`, `numpy`, `openpyxl`.

## Utilisation

Lancer les scripts **dans cet ordre** depuis la racine du projet :

```powershell
# 1. Nettoyer les données et produire data_clean/stays_basic_info_2010_clean.csv
python src/clean.py

# 2. Calculer la fréquentation et séparer hubs / petits ports
python src/cluster.py

# 3. Explorer les distances entre types de ports (A, L, T) et ports P
python src/exploration_test.py
```

## État d'avancement

- [x] Nettoyage des séjours et jointure avec le référentiel ports
- [x] Calcul de fréquentation par port
- [x] Séparation hubs majeurs (≥ 100 séjours) / petits ports
- [x] Exploration des distances Haversine par type de port
- [ ] Fusion géographique des petits ports
- [ ] Validation sur des cas concrets (top 20 ports, GPS manquants, etc.)

## Notes

Voir le dossier `notes/` pour le contexte métier et les rappels techniques (pandas, pathlib, vectorisation).
