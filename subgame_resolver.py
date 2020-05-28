import numpy as np
from tree_parser import *
from game_solver import *


if __name__ == "__main__":
    
    tree,id_dic,infosets,_,infoset_id_of,fake_infosets,fake_id_of = gen_strats()
    context2 = Context(infosets,infoset_id_of,id_dic)
    resolver(tree)
    
    

#Visita in profondità i primi n nodi (con n = subgame_size) e ritorna visited che è un set di questi nodi
#new_roots è il set di nodi da considerare come radici per i subgame seguenti
#subgame_size è l'altezza del subgame considerato

def dfs_limited(tree, visited=None, counter=0, new_roots=None):
    if visited == None:
        visited = set()
        new_roots = set()
    visited.add(tree)
    counter = counter + 1
    if counter <= subgame_size:
        for child in tree.children:
            dfs_limited(child, visited, counter)
    else:
        new_roots.add(tree.children)
    
    return visited, new_roots
    

#Costruisce un subgame valido costituito dai nodi apparteneti agli stessi information set dei 
#nodi nel set visited 
def build_subgame(visited):
    
    subgame_infosets = set()
    subgame = set()
    for tree in visited:
        if tree.infoset not in subgame_infosets:
            subgame_infosets.add(tree.infoset)
    for infoset in subgame_infosets:
        subgame.add(infosets.get(infoset))
        
    return subgame
        
#Dato il subgame applico cfr ai suoi nodi  
def cfr_subgame(subgame):
    n_iterations = 20000
    for tree in subgame:
        [do_iteration(tree,i,context2,infosets) for i in range(0,n_iterations)]
        
    #bisogna fare back map?
        
        
#Decidere valore limit e subgame size
def resolver(tree, subgame_size = 3, limit = 10):
 
    visited, new_roots = dfs_limited(tree)
    subgame = build_subgame(visited)
    cfr_subgame(subgame)
    
    for i in range(subgame_size, limit + 1):
        for tree in new_roots:
            visited, new_roots = dfs_limited(tree)
            subgame = build_subgame(visited)
            cfr_subgame(subgame)
