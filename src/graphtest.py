import networkx as nx

G = nx.Graph()
G.add_edge("A", "B")
G.add_edge("B", "C")
G.add_edge("D", "E")
G.add_edge("F", "G")  # composante séparée

print(nx.number_connected_components(G))  # → 2