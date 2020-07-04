import numpy as np
from tree_parser import *
from game_solver import *

def copynode(x):
    xp=Tree(x.node_id,x.children,x.line,x.action_label,x.infoset)
    xp.action_infoset_label=x.action_infoset_label
    xp.abstracted_infoset=x.abstracted_infoset
    xp.abstract_action_infoset_label=x.abstract_action_infoset_label
    if(hasattr(x,'player_id')):
        xp.player_id=x.player_id
    if(hasattr(x,'father_id')):
        xp.father_id=x.father_id
    return xp
def deepcopia(nodes):
    if isinstance(nodes,list):
        acc=[]
        for x in nodes:
            acc.append(copynode(x))
        return acc

    #node_id,children,line,action_label,infoset
    #self.children=children
    #self.node_id=node_id
    #self.line=line
    #self.action_label=action_label
    #self.infoset=infoset
    #self.action_infoset_label=""
    #self.abstracted_infoset=""
    #self.abstract_action_infoset_label=""
    return copynode(nodes)

def find_probability(tree,x,id_dic,denorm_factor):
    curr=x
    prob=1.00
    while(curr!=tree):
        #print("prob %f"%prob)
        label=curr.action_label
        prev=curr
        curr=id_dic[curr.father_id]
        if(curr.isNature()):

            num_c=len(curr.children)
            probs=curr.line[4:]
            prob_func=lambda i:float(probs[i].split("=")[1])/num_c
            for i,child in enumerate(curr.children):
                probability=float(probs[i].split("=")[1])/num_c
                if(child.node_id==prev.node_id):
                    #print("Nature %f %f"%(probability,float(probs[i].split("=")[1])/num_c))
                    prob*=probability
                    break
        else:
            prob*=curr.infoset.strategy[label]
    #print("PROB %f"%prob)
    return prob*denorm_factor

#infoset_id_of contiene un dizionario che, dato un id di nodo, restituisce un oggetto Infoset
#infosets contiene un dizionario che, dato un oggetto Infoset, restituisce una lista di id di nodi
#infoset_of contiene un dizionario che, data una stringa di sequenza di gioco, restituisce un Infoset
#
#Ritorna una lista di figli copiati,saltando le azioni del giocatore player_id
def copy_subtree(tree,player_id,infosets,id_of,id_dic,original_infosets):
    copied_children=[]
    if(tree.isTerminal()):#No children
        return []
    else:
        #Per ogni figlio, ritorna quello se è dell'altro giocatore, saltalo altrimenti
        for child in tree.children:
            #Questo va mancato e bisogna ritornare i figli suoi
            if(hasattr(child,'player_id') and child.player_id==player_id):
                cop_children=(copy_subtree(child,player_id,infosets,id_of,id_dic,original_infosets))
                for grandson in cop_children:
                    grandson.action_label=child.action_label
                copied_children+=cop_children

            else:
                copied_child=deepcopia(child)
                copied_children.append(copied_child)
                if(child.isTerminal()):
                    continue

                id_dic[copied_child.node_id]=copied_child
                id_of[copied_child.node_id]=copied_child.infoset
                copied_child.children=copy_subtree(copied_child,player_id,infosets,id_of,id_dic,original_infosets)
                #TODO infoset dei natura?
                if(not child.isNature()):
                    if(child.infoset not in infosets):
                        #print("PUSHING INFOSET %s"% child.infoset)
                        infosets[child.infoset]=original_infosets[child.infoset].copy()
                    else:
                        1
                        #print("NOT PUSHING INFOSET %s"% child.infoset)

    #print("Copied %s : %s"%(tree.node_id, [x.node_id for x in copied_children]))
    return copied_children

def copy_tree(original_root,original_infosets,original_id_dic,subgame_roots, subgame, player_id):
    #other_player=(player_id+1)%2
    #Crea nodo natura
    #Copia le radici
    #Linka le radici
    #Copia i figli solo se non di player aggiornando le prob con la blueprint
    infosets={}
    id_dic={}
    id_of={}
    subgame=deepcopia(subgame)
    subgame_roots=deepcopia(subgame_roots)

    sub_leaf_children=[]
    root_infoset=Infoset("Fake root",-1)

    #self, node_id,children,line,action_label,infoset):
    fakeline=["fakeline","fakeline2","chance",""]
    for r in subgame_roots:
        fakeline.append(r.action_label+"="+str(find_probability(original_root,r,original_id_dic,len(subgame_roots))))

    root=Tree("Root",subgame_roots ,fakeline,"",root_infoset)
    id_dic[root.node_id]=root
    infosets[root_infoset]=[root.node_id]
    id_of[root.node_id]=root_infoset

    sub_leaf=[]
    #For each root
    for x in subgame_roots:
        a_label="root-"+x.node_id
        x.action_label=a_label
        root_infoset.actions.add(a_label)

        #prob=find_probability(original_root,x)
        #root_infoset.strategy[a_label]=prob
        if(not x.infoset in infosets):
            infosets[x.infoset]=original_infosets[x.infoset].copy()

        id_dic[x.node_id]=x
        id_of[x.node_id]=x.infoset

        if(len(x.children)>0 and x.children[0] not in subgame):
            sub_leaf_children+=x.children
            sub_leaf.append(x)


    #Copy subgame as it is
    print("Processing %d nodes in subgame"%len(subgame))
    for x in subgame:
        id_dic[x.node_id]=x
        if(x.isTerminal()):
            continue
        id_of[x.node_id]=x.infoset
        if(not x.infoset in infosets):
            infosets[x.infoset]=original_infosets[x.infoset].copy()

        if(len(x.children)>0 and x.children[0] not in subgame):
            sub_leaf_children+=x.children
            sub_leaf.append(x)

    #Copy rest of the game just of other player
    print("Processing %d children of subgame leaves"% len(sub_leaf))
    for node in sub_leaf:
        node.children=copy_subtree(node,player_id,infosets,id_of,id_dic,original_infosets)

    return root,infosets,id_of,id_dic,sub_leaf


def calc_subgame(roots,size):
    nodes=[]
    for i in range(1, size):
        children=[y for y in [x.children for x in roots if (len(x.children))>0]]
        if(len(children)==0):
            break
        children=reduce(lambda x,y: x+y, children)
        #print("Children %s"%children)
        nodes+=children
        roots=children
    #print("DEBUG NODES IS %s"%nodes)
    return nodes

def copy_sub(node,original_infosets,infosets,id_of,id_dic,new_subgame,old_subgame):
    if node.isTerminal():
        return []

    if not node.isNature():
        if node.infoset not in infosets:
            infosets[node.infoset]=original_infosets[node.infoset].copy()

    acc=[]
    for child in node.children:
        child_c=deepcopia(child)
        if(child in old_subgame):
            new_subgame.append(child_c)
        child_c.children=copy_sub(child_c,original_infosets,infosets,id_of,id_dic,new_subgame,old_subgame)
        acc.append(child_c)
        if(not child_c.isNature() and not child_c.isTerminal()):
            id_of[child_c.node_id]=child_c.infoset
        id_dic[child_c.node_id]=child_c

    return acc

def copy_tree2(original_root,original_infosets,original_id_dic,subgame_roots,subgame, player_id):
    infosets={}
    id_dic={}
    id_of={}
    subgame_roots=deepcopia(subgame_roots)

    sub_leaf_children=[]
    root_infoset=Infoset("Fake root",-1)

    #self, node_id,children,line,action_label,infoset):
    fakeline=["fakeline","fakeline2","chance",""]
    for r in subgame_roots:
        fakeline.append(r.action_label+"="+str(find_probability(original_root,r,original_id_dic,len(subgame_roots))))

    root=Tree("Root",subgame_roots ,fakeline,"",root_infoset)
    id_dic[root.node_id]=root
    infosets[root_infoset]=[root.node_id]
    id_of[root.node_id]=root_infoset

    new_subgame=[]
    sub_leaf=[]
    #For each root
    subgame=set(subgame)
    for x in subgame_roots:
        a_label="root-"+x.node_id
        x.action_label=a_label
        root_infoset.actions.add(a_label)

        #prob=find_probability(original_root,x)
        #root_infoset.strategy[a_label]=prob
        if(not x.infoset in infosets):
            infosets[x.infoset]=original_infosets[x.infoset].copy()

        id_dic[x.node_id]=x
        id_of[x.node_id]=x.infoset

        x.children=copy_sub(x,original_infosets,infosets,id_of,id_dic,new_subgame,subgame)
    subgame_ids=set([y.node_id for y in subgame])
    for x in new_subgame+subgame_roots:
        if(len(x.children)>0 and x.children[0].node_id not in subgame_ids):
            sub_leaf_children+=x.children
            sub_leaf.append(x)
    return new_subgame,subgame_roots,root,infosets,id_of,id_dic,sub_leaf

def refine2(player,tree,infosets,infoset_id_of,id_dic,n_iterations):
    limit=1
    size=100
    roots=tree.children
    print(roots[0].infoset.actions)
    print(tree.line[4:])
    print("Refining %s"%roots)
    val=0
    for i in range(1, limit+1):#nolimits
        infoset_strategy_backup={info: info.strategy.copy() for info in infosets.keys()}
        print("Building subgame")
        subgame=calc_subgame(roots,size)
        subgame_infosets=[x.infoset for x in roots+subgame if hasattr(x,'player_id') and x.player_id==str(player)]
        #print(subgame_infosets)
        print("Copying tree")
        subgame,roots,new_tree,sub_infosets,sub_id_of,sub_id_dic,sub_leaves=copy_tree2(tree,infosets,id_dic,roots,subgame,player)

        context=Context(sub_infosets,sub_id_of,sub_id_dic)

        context.init_matrices(True)

        print("Debug:")
        print("Infosets: %s"%sub_infosets)
        print()
        print("Id of: %s"%sub_id_of)
        print()
        print("Id dic: %s"%sub_id_dic)
        total_sub=set(subgame+roots+[new_tree])
        for node in total_sub:
            node.marked=True
        val=[do_iteration(new_tree,j,context,sub_infosets,total_sub,player) for j in range(0,n_iterations)][-1]
        x=subgame+roots+[new_tree]
        print(len(x))

        for infoset in sub_infosets:
            get_average_strategy(infoset,context)
            clean_strategy(infoset,context,2)
            infoset.strategy=infoset.next_strategy

        print("Restoring information sets outside subgame")
        for info in infosets.keys():
            if not info in subgame_infosets:
                info.strategy=infoset_strategy_backup[info]
        print("Updating roots after iteration %d" %i)
        #Nodi natura?
        roots_nest=[x.children for x in sub_leaves]
        # print("Old roots %s"%[x.node_id for x in roots])
        # print("Old leaves %s"%[x.node_id for x in sub_leaves])
        if(len(roots_nest)==0):
            print("Finished tree at iteration %d"%i)
            break
        roots=reduce(lambda x,y: x+y, roots_nest)
        roots=[x for x in roots if not x.isTerminal()]
        if(len(roots)==0):
            print("Finished tree at iteration %d"%i)
            break
        print("New Roots %d %s"%(len(roots),[x.node_id for x in roots]))
    return val

if __name__ == "__main__":
    start_time=time.time()
    init_n=2
    refine_n=2
    tree,id_dic,infosets,infoset_id_of,val,fake_infosets = gen_strats("Leduc_C.txt",init_n)
    val=refine2(1,tree,infosets,infoset_id_of,id_dic,refine_n)
    output_strategy("strategy_refined.txt",infosets,infoset_id_of,id_dic,val,len(infosets),len(fake_infosets))
    val=refine2(2,tree,infosets,infoset_id_of,id_dic,refine_n)
    output_strategy("strategy_refined2.txt",infosets,infoset_id_of,id_dic,val,len(infosets),len(fake_infosets))
    #Todo check finale(meglio string based, che le probabilità sommino a uno)
    print("Total exec time: %s seconds"%(time.time()-start_time))
