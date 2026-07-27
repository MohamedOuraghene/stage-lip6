from pathlib import Path

# =============================================================================
# 1. CHEMINS DE DOSSIERS (Arborescence dynamique du projet)
# =============================================================================
# Racine du projet (dossier parent de src/)
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_CLEAN_DIR = BASE_DIR / "data_clean"
RESULTS_DIR = BASE_DIR / "results"
FIGURES_DIR = BASE_DIR / "reports" / "figures"

# Création automatique des dossiers de sortie s'ils n'existent pas
for directory in [DATA_CLEAN_DIR, RESULTS_DIR, FIGURES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# =============================================================================
# 2. FICHIERS D'ENTRÉE FIXES
# =============================================================================
MATCHING_PORTS_FILE = DATA_DIR / "Matching_ports_city1_city2.xlsx"

# =============================================================================
# 3. HYPERPARAMÈTRES DU MOTEUR DU STREAM GRAPH
# =============================================================================
# Clustering Spatial (UNCLOS)
RAYON_MAX_KM = 44.0  # Rayon de la zone contiguë (24 milles nautiques)
POURCENTAGE_SEUIL_HUB = 0.005  # Seuil de trafic pour être un hub autonome (0.5%)
LINKAGE_METHOD = "complete"  # Hierarchical clustering complete linkage

# Reconstruction Temporelle
DELTA_T_DAYS = 30  # Fenêtre max de transit valide (30 jours)

# Métrologie & Connexité G_Δ
WINDOW_DAYS_CONNECTIVITY = 14  # Fenêtre de discrétisation (14 jours)