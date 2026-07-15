- Un dataframe c'est un tableau qui provient du modules pandas qui a des lignes, des colonnes et un index. C'est comme une table en SQL.

- Une série c'est en gros un dataframe à une colonne même si c'est différent.

- Un masque booléen c'est une série de True/False

- les [...] apres le nom d'un dataframe en Python ont 2 roles :
 1) Si tu lui donnes du texte genre dataframelambda["Name"] -> te donne uniquement la colonne des noms
                                    dataframelambda[["Name","Poids"]] -> te donne un sous tableau avec les colonnes
 2) Si tu lui donnes un masque booléen, là Pandas comprend que tu veux sélectionner des lignes horizontales
donc dataframelambda[masque] te gardera seulement les lignes ou le masque vaut True



















- Réseau scale-free: quelques hubs ont la majorité des noeuds ont peu de connexions mais quelques noeuds (hubs) disposent de bcp de connexion, elle suit une loi puissance mathématique. (y'a d'autres types de réseaux intéressants)