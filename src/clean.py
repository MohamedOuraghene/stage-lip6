import pandas as pd
from pathlib import Path

def clean_data():
    base_dir = Path(__file__).resolve().parent.parent
    csv_path = base_dir / "data" / "stays_basic_info_2010.csv"
    matching_path = base_dir / "data" / "Matching_ports_city1_city2.xlsx"
    output_dir = base_dir / "data_clean"
    output_path = output_dir / "stays_basic_info_2010_clean.csv"

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Chargement et nettoyage colonnes
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    # 2. Conversion des dates
    df["ARRIVAL DATE"] = pd.to_datetime(df["ARRIVAL DATE"], format="%d/%m/%Y")
    df["SAILING DATE"] = pd.to_datetime(df["SAILING DATE"], format="%d/%m/%Y")

    # 3. Durée de séjour
    df["STAY DURATION DAYS"] = (df["SAILING DATE"] - df["ARRIVAL DATE"]).dt.days

    # 4. Jointure avec le dictionnaire des ports
    matching = pd.read_excel(matching_path)
    # Dans src/clean.py
    matching_clean = matching[["ID_Lloyds", "Name_Final", "COUNTRY", "X1", "Y1", "Type"]].drop_duplicates(subset="ID_Lloyds")

    print(matching["Type"].value_counts())
    print(matching["Analysis1"].value_counts().head(20))

    print(matching[matching["ID_Lloyds"].isin([2581, 1584, 1740, 5717])][["ID_Lloyds", "Name_Final", "Type"]])

    # Vérification si y'a des ports sans Type
    print(f"Ports avec un Type : {matching['Type'].notna().sum()} / {len(matching)}")
    print(f"Ports sans Type : {matching['Type'].isna().sum()}")

    df_clean = pd.read_csv(base_dir / "data_clean" / "stays_basic_info_2010_clean.csv")
    print(f"Séjours avec un Type : {df_clean['Type'].notna().sum()} / {len(df_clean)}")
    print(f"Séjours sans Type : {df_clean['Type'].isna().sum()}")
    
    # On renomme pour éviter les doublons de colonnes inutiles
    df = df.merge(matching_clean, left_on="PLACE ID", right_on="ID_Lloyds", how="left")
    df = df.drop(columns=["ID_Lloyds"]) # Nettoyage de la colonne en double

    # 5. Sauvegarde
    df.to_csv(output_path, index=False)
    print(f"✓ Données nettoyées et sauvegardées ({len(df)} lignes) -> {output_path}")

if __name__ == "__main__":
    clean_data()

