import pandas as pd
import numpy as np
from pathlib import Path

def haversine_vectorized(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

base_dir = Path(__file__).resolve().parent.parent
matching_path = base_dir / "data" / "Matching_ports_city1_city2.xlsx"
matching = pd.read_excel(matching_path)

ports = matching[matching["Type"] == "P"][["ID_Lloyds", "Name_Final", "X1", "Y1"]].drop_duplicates(subset="ID_Lloyds").dropna(subset=["X1", "Y1"])
anchorages = matching[matching["Type"] == "A"][["ID_Lloyds", "Name_Final", "X1", "Y1"]].drop_duplicates(subset="ID_Lloyds").dropna(subset=["X1", "Y1"])

ports_lat = ports["Y1"].values
ports_lon = ports["X1"].values

def explore_distances(types=["A", "L", "T"]):
    for type_code in types:
        subset = matching[matching["Type"] == type_code][["ID_Lloyds", "Name_Final", "X1", "Y1"]].drop_duplicates(subset="ID_Lloyds").dropna(subset=["X1", "Y1"])
        
        distances_min = []
        for _, row in subset.iterrows():
            d = haversine_vectorized(row["Y1"], row["X1"], ports_lat, ports_lon)
            distances_min.append(d.min())
    
        subset = subset.copy()
        subset["DIST_PORT_PLUS_PROCHE"] = distances_min
    
        print(f"\n=== Type {type_code} ===")
        print(subset["DIST_PORT_PLUS_PROCHE"].describe())
        print(f"< 5km  : {(subset['DIST_PORT_PLUS_PROCHE'] <= 5).sum()} / {len(subset)}")
        print(f"< 10km : {(subset['DIST_PORT_PLUS_PROCHE'] <= 10).sum()} / {len(subset)}")
        print(f"< 25km : {(subset['DIST_PORT_PLUS_PROCHE'] <= 25).sum()} / {len(subset)}")
        print(f"< 50km : {(subset['DIST_PORT_PLUS_PROCHE'] <= 50).sum()} / {len(subset)}")

    terminals = matching[matching["Type"] == "T"][["Name_Final", "COUNTRY", "X1", "Y1"]].dropna()
    print(terminals.head(20))


if __name__ == "__main__":
    explore_distances()

