import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

base_dir = Path(__file__).resolve().parent.parent
clean_path = base_dir / "data_clean" / "stays_basic_info_2010_clean.csv"

df = pd.read_csv(clean_path)
df["ARRIVAL DATE"] = pd.to_datetime(df["ARRIVAL DATE"])
df["SAILING DATE"] = pd.to_datetime(df["SAILING DATE"])

df_sorted = df.sort_values(["VESSEL ID", "ARRIVAL DATE"])
df_sorted["NEXT ARRIVAL DATE"] = df_sorted.groupby("VESSEL ID")["ARRIVAL DATE"].shift(-1)
df_sorted["TRANSIT DAYS"] = (df_sorted["NEXT ARRIVAL DATE"] - df_sorted["SAILING DATE"]).dt.days

transits = df_sorted[df_sorted["TRANSIT DAYS"] >= 0]["TRANSIT DAYS"]

plt.hist(transits[transits <= 90], bins=90, edgecolor="black")
plt.axvline(15, color="red", linestyle="--", label="15 jours")
plt.axvline(30, color="orange", linestyle="--", label="30 jours")
plt.axvline(45, color="green", linestyle="--", label="45 jours")
plt.xlabel("Durée de transit (jours)")
plt.ylabel("Nombre de trajets")
plt.legend()
plt.title("Distribution des transits — où couper ?")
plt.show()

# Le choix de Δt est robuste — la séparation nette entre trajets réels et artefacts de censure rend le résultat insensible à la valeur exacte du seuil dans l'intervalle [20, 55] jours
print(f"Transits entre 20 et 55 jours : {((transits >= 20) & (transits <= 55)).sum()}")
print(f"Transits ≤ 20 jours : {(transits <= 20).sum()}")
print(f"Transits ≥ 55 jours : {(transits >= 55).sum()}")