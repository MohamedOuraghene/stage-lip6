import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

base_dir = Path(__file__).resolve().parent.parent
csv_path = base_dir / "data" / "stays_basic_info_2010.csv"
output_dir = base_dir / "data_clean"
output_path = output_dir / "stays_basic_info_2010_clean.csv"
matching_path = base_dir / "data" / "Matching_ports_city1_city2.xlsx"

output_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(csv_path)
df.columns = df.columns.str.strip()

# --- Conversion des dates ---
df["ARRIVAL DATE"] = pd.to_datetime(df["ARRIVAL DATE"], format="%d/%m/%Y")
df["SAILING DATE"] = pd.to_datetime(df["SAILING DATE"], format="%d/%m/%Y")

# --- Durée de séjour en jours ---
df["STAY DURATION DAYS"] = (df["SAILING DATE"] - df["ARRIVAL DATE"]).dt.days

# --- Jointure avec les noms de ports ---
matching = pd.read_excel(matching_path)
matching_clean = matching[["ID_Lloyds", "Name_Final", "COUNTRY", "X1", "Y1"]].drop_duplicates(subset="ID_Lloyds")
df = df.merge(matching_clean, left_on="PLACE ID", right_on="ID_Lloyds", how="left")

# --- Sauvegarde ---
df.to_csv(output_path, index=False)

print(f"✓ Lignes traitées : {len(df)}")
print(f"✓ Séjours à 0 jour : {(df['STAY DURATION DAYS'] == 0).sum()} / {len(df)}")
print(f"✓ Fichier écrit : {output_path}")

# --- Histogramme durées de séjour ---
df_plot = df[(df["STAY DURATION DAYS"] >= 0) & (df["STAY DURATION DAYS"] <= 30)]
plt.hist(df_plot["STAY DURATION DAYS"].dropna(), bins=31, edgecolor="black")
plt.xlabel("Durée de séjour (jours)")
plt.ylabel("Nombre de navires")
plt.title("Distribution des durées de séjour à quai (≤ 30 jours)")
plt.show()

# --- Calcul des transits ---
df_sorted = df.sort_values(["VESSEL ID", "ARRIVAL DATE"])
df_sorted["NEXT ARRIVAL DATE"] = df_sorted.groupby("VESSEL ID")["ARRIVAL DATE"].shift(-1)
df_sorted["NEXT PLACE ID"] = df_sorted.groupby("VESSEL ID")["PLACE ID"].shift(-1)
df_sorted["TRANSIT DAYS"] = (df_sorted["NEXT ARRIVAL DATE"] - df_sorted["SAILING DATE"]).dt.days

# --- Histogramme durées de transit ---
df_plot = df_sorted[(df_sorted["TRANSIT DAYS"] >= 0) & (df_sorted["TRANSIT DAYS"] <= 60)]
plt.hist(df_plot["TRANSIT DAYS"].dropna(), bins=60, edgecolor="black")
plt.xlabel("Durée de transit (jours)")
plt.ylabel("Nombre de trajets")
plt.title("Distribution des durées de transit entre ports (≤ 60 jours)")
plt.show()

# --- Fréquentation des ports ---
frequentation = df.groupby(["PLACE ID", "Name_Final", "COUNTRY"]).size().sort_values(ascending=False)
print("Top 20 des ports les plus fréquentés en 2010 :")
print(frequentation.head(20))

print(df_sorted[df_sorted["TRANSIT DAYS"] >= 0]["TRANSIT DAYS"].describe())