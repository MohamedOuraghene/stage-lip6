from pathlib import Path
import pandas as pd

# Import de la configuration centralisée
from src.config import DATA_CLEAN_DIR, DATA_DIR, MATCHING_PORTS_FILE


def clean_data(year=2010):
    output_path = DATA_CLEAN_DIR / f"stays_basic_info_{year}_clean.parquet"

    # Liste de tous les motifs de noms de fichiers possibles pour l'année
    candidates = [
        DATA_DIR / f"{year}_MOVES.csv",
        DATA_DIR / f"{year}_MOVES.csv.gz",
        DATA_DIR / f"MOVES_{year}.csv",
        DATA_DIR / f"MOVES_{year}.csv.gz",
        DATA_DIR / f"MOVES_{year}.xlsx",
        DATA_DIR / f"{year}_MOVES.xlsx",
        DATA_DIR / f"stays_basic_info_{year}.csv",
    ]

    input_file = None
    for filepath in candidates:
        if filepath.exists():
            input_file = filepath
            break

    if input_file is None:
        print(f"Erreur : Aucun fichier trouvé pour l'année {year} dans {DATA_DIR}")
        return None

    print(f"Chargement du fichier : {input_file.name}...")

    # Lecture selon l'extension du fichier
    if input_file.suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(input_file)
    else:
        df = pd.read_csv(input_file, low_memory=False)

    # Nettoyage des colonnes
    df.columns = df.columns.str.strip()

    # Conversion flexible des dates
    df["ARRIVAL DATE"] = pd.to_datetime(
        df["ARRIVAL DATE"], dayfirst=True, errors="coerce"
    )
    df["SAILING DATE"] = pd.to_datetime(
        df["SAILING DATE"], dayfirst=True, errors="coerce"
    )

    # Filtrer les dates invalides
    df = df.dropna(subset=["ARRIVAL DATE", "SAILING DATE"]).copy()

    # Calcul de la durée de séjour
    df["STAY DURATION DAYS"] = (
        df["SAILING DATE"] - df["ARRIVAL DATE"]
    ).dt.days
    df = df[df["STAY DURATION DAYS"] >= 0].copy()

    # Jointure avec le dictionnaire des ports
    matching = pd.read_excel(MATCHING_PORTS_FILE)
    matching_clean = matching[
        ["ID_Lloyds", "Name_Final", "COUNTRY", "X1", "Y1", "Type"]
    ].drop_duplicates(subset="ID_Lloyds")

    df = df.merge(
        matching_clean, left_on="PLACE ID", right_on="ID_Lloyds", how="left"
    )
    df = df.drop(columns=["ID_Lloyds"], errors="ignore")

    print(f"\n--- Diagnostic Année {year} ---")
    print(f"• Total mouvements valides : {len(df)}")
    print(f"• Ports uniques actifs : {df['PLACE ID'].nunique()}")
    print(f"• Navires uniques actifs : {df['VESSEL ID'].nunique()}")

    df.to_parquet  (output_path, index=False)
    print(f"✓ Fichier nettoyé sauvegardé : {output_path}\n")
    return df


if __name__ == "__main__":
    clean_data(year=2010)
    clean_data(year=2002)

    # Test d'inspection 2002 en utilisant le chemin robuste via DATA_CLEAN_DIR
    file_2002 = DATA_CLEAN_DIR / "stays_basic_info_2002_clean.parquet"
    if file_2002.exists():
        df_2002 = pd.read_parquet(file_2002)
        df_2002["ARRIVAL DATE"] = pd.to_datetime(df_2002["ARRIVAL DATE"])
        print("=== Répartition des arrivées par mois en 2002 ===")
        print(df_2002["ARRIVAL DATE"].dt.month.value_counts().sort_index())