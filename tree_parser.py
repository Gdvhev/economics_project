import csv
from graphviz import *
import numpy as np
from sklearn.cluster import *
infoset_id=1
def gen_infoset(dict,player):
    global infoset_id
    i=0
    id=str(infoset_id)
    infoset_id+=1
    while(player+"."+str(i) in dict):
        i=i+1
    return Infoset(player+"."+str(i),id)

def calc_utility(tree_node):
    if(tree_node.line[2]!="leaf"):
        return 0
    utility=float(str(tree_node.line[4]).split("=")[1])
    return utility

class Infoset:
    def __init__(self, info_string, id):
        self.info_string=info_string
        self.id=id
        self.abstracted_infoset=""

class Tree:
    def __init__(self, node_id,children,line,action_label,infoset):
        self.children=children
        self.node_id=node_id
        self.line=line
        self.action_label=action_label
        self.infoset=infoset
        self.action_infoset_label=""
        self.abstracted_infoset=""

    def isTerminal(self):
        return self.line[2]=="leaf"
    def build_dot(self,dot,father_id):
        #dot.node(self.node_id,self.node_id+" Player "+str(self.player_id))
        #player_id="Nature" if (self.line[2]=="chance") else ("Player "+self.line[3])
        label=self.node_id
        if(self.line[2]=="chance"):#Nature
            label=label+" Nature\n "+str(self.line[4:])
        elif(self.line[2]=="leaf"):#Terminal Node
            label=label+" Terminal\n trace: "+self.line[1]+"\n "+str(self.line[3:])
        else: #Player node
            player_id="Player "+self.line[3]
            label=label+" infoset:"+self.infoset.info_string+" "+self.infoset.id+ " "+player_id+"\n "+self.line[1]+"\n "+str(self.line[4:])
        #dot.node(self.node_id,self.node_id+" "+player_id+str(self.line))
        dot.node(self.node_id,label)
        dot.edge(father_id, self.node_id,label=(self.action_label+self.action_infoset_label))
        for child in self.children:
            child.build_dot(dot,self.node_id)

    def fill_infoset_dictionary(self,dict,father_infoset):
        player_id="P"
        if(self.line[2]!="leaf"):#Nature or Terminal
            if(self.line[2]!="chance"):
                player_id=self.line[3]
            else:
                player_id="N"
            if(self.infoset=="NaN"):
                self.infoset=gen_infoset(dict,player_id)
                dict[self.infoset]=[self.node_id]
            elif(self.infoset in dict):
                dict[self.infoset].append(self.node_id)
            else:
                dict[self.infoset]=[self.node_id]

        for child in self.children:
            child.fill_infoset_dictionary(dict,self.infoset)

        if(father_infoset=="NaN"):
            print(self.line)

        self.action_label=self.action_label
        self.action_infoset_label=str(father_infoset.id)

    def fill_sequence_form(self,seq_dic,player_history,probability,natureson,father_player):
        if(not natureson):
            old=player_history[father_player]

            player_history[father_player]=player_history[father_player]+ self.action_label

        if(self.line[2]!="chance" and self.line[2]!="leaf"):
            #Player node
            player_id=self.line[3]
            for child in self.children:
                child.fill_sequence_form(seq_dic,player_history,probability,False,player_id)


        elif(self.line[2]== "leaf"):
            utility=float(str(self.line[4]).split("=")[1]) * probability
            #Leaf

            if(player_history["1"] in seq_dic.keys()):
                seq_dic[player_history["1"]][player_history["2"]]=utility
            else:
                seq_dic[player_history["1"]]={player_history["2"] : utility}

        else:
            num_c=len(self.children)
            probs=self.line[4:]
            for i in range(0,len(self.children)):
                my_probability=probability * float(probs[i].split("=")[1])
                self.children[i].fill_sequence_form(seq_dic,player_history,my_probability/num_c,True,"N")

        if(not natureson):
            player_history[father_player]=old


    def calculate_outcome_vector(self,out_vector):
        if(self.line[2]== "leaf"):
            out_vector.append(calc_utility(self))

        else:
            for child in self.children:
                child.calculate_outcome_vector(out_vector)


        return "A",out_vector#Placeholder per l'analisi strutturale

def cluster_and_recur(actions,infoset_of,fake_infosets,fake_id_of,children,vectors,children_infosets):
    if(len(vectors)<2):
        print("Skipping %s as lone vector"%vectors)
        return
    global infoset_id
    #magic number 0.27
    eps=0.6*len(vectors)#TODO valore
    clustering = KMeans(n_clusters=2).fit(vectors)
    print("Cluster targets: %s" %clustering.labels_)

    fake_info_store={}
    for index,obj in enumerate(clustering.labels_):
        if(obj=="-1"):
            print("Outliers not supported ffs")
            print(1/0)

        if(not obj in fake_info_store):
            fake_infoset=Infoset("",str(infoset_id))
            infoset_id=infoset_id+1
            fake_info_store[obj]=fake_infoset
            fake_infosets[fake_infoset]=[]

        else:
            fake_infoset=fake_info_store[obj]

        children_infosets[index].abstracted_infoset=fake_infoset
        fake_infoset.info_string=fake_infoset.info_string+"+"+children_infosets[index].info_string


    for child in children:
        if(child.infoset.abstracted_infoset!=""):
            child.abstracted_infoset=child.infoset.abstracted_infoset
            fake_id_of[child.node_id]=child.abstracted_infoset
            fake_infosets[child.abstracted_infoset].append(child.node_id)
    #print(fake_id_of)
    #print(fake_info_store)
    #print(fake_infosets)
    print("Children infosets")
    for children_infoset in children_infosets:
        print(children_infoset.info_string)
    print("Children")
    for child in children:
        print(child.line)
    #Ripeti per ogni gruppo di figli di ogni information set astratto o che non è stato astratto
    abstracted_infosets=list(fake_info_store.values())
    unused_infosets=[infoset for infoset in children_infosets if infoset.abstracted_infoset==""]
    recur_infosets=unused_infosets +abstracted_infosets
    children_store={ i : {j:[] for j in actions} for i in recur_infosets }

    #print(children_store)
    print("Abstracted infosets")
    for infoset in abstracted_infosets:
        print(infoset)
        print(infoset.info_string)
    for child in children:
        cinfoset=child.infoset

        for action in actions:
            grandsons=[grandson for grandson in child.children if not grandson.isTerminal() and grandson.action_label==action ]
            if(cinfoset.abstracted_infoset==""):
                children_store[cinfoset][action]=children_store[cinfoset][action]+grandsons
            else:
                if(not cinfoset.abstracted_infoset in abstracted_infosets):
                    print(cinfoset in unused_infosets)
                    print(cinfoset.info_string)
                    print(cinfoset.abstracted_infoset.info_string)
                    print(cinfoset.abstracted_infoset)
                children_store[cinfoset.abstracted_infoset][action]=children_store[cinfoset.abstracted_infoset][action]+grandsons

    print("----------Children store is----------")
    print(children_store)
    print("----------------------------------")
    for _,store in children_store.items():
        print()
        for _,children_list in store.items():
            #print(children_list)
            gen_infoset_clusters(actions,infoset_of,fake_infosets,fake_id_of,children_list)

def gen_infoset_clusters(actions,infoset_of,fake_infosets,fake_id_of,children):
    if(len(children)<2):
        return
    children_infosets=[]
    print("----------Children is----------")
    print(children)
    print("------------------------------")
    for child in children:
        if(infoset_of[child.node_id] not in children_infosets):
            children_infosets.append(infoset_of[child.node_id])

    #print(children_infosets)
    if(len(children_infosets)<2):
        return

    outcome_matrix={}
    relevant_matrix={}
    relevant_infosets_matrix={}
    for infoset in children_infosets:
        vector=[]
        relevant_children=[]
        for child in children:
            if(infoset == infoset_of[child.node_id]):
                _, cv =child.calculate_outcome_vector([])
                vector=vector+cv
                relevant_children.append(child)
        if(len(vector) not in outcome_matrix):
            outcome_matrix[len(vector)]=[]
            relevant_matrix[len(vector)]=[]
            relevant_infosets_matrix[len(vector)]=[]
        outcome_matrix[len(vector)].append(vector)
        relevant_matrix[len(vector)]+=(relevant_children)
        relevant_infosets_matrix[len(vector)].append(infoset)

    #X = np.array([[1, 2], [2, 5], [3, 6],
    #    [8, 7], [8, 8], [7, 3], [1, 2], [15, 15]])
    #hundred = lambda t: t * 100
    #outcome_matrix["struttura_default"][2]=[x*200000000 for x in outcome_matrix["struttura_default"][2]]

    for size,vectors in outcome_matrix.items():
        print(vectors)
        cluster_and_recur(actions,infoset_of,fake_infosets,fake_id_of,relevant_matrix[size],vectors,relevant_infosets_matrix[size])

    #size=len(outcome_matrix["struttura_default"][0])
    #print("Size is %2d"% size)

    # error=False
    # for vector in outcome_matrix["struttura_default"]:
    #     #assert(len(vector)==size)
    #     if(len(vector)!=size):
    #         error=True
    #         break
    # if(error):
    #     print("__________AN Error has been found________")
    #     print([child.line for child in children])
    #     return


def add_infoset_edges(dot,infosets,abstracted_infosets):
    for infoset,nodes in infosets.items():
        if(len(nodes)>1):
            prev=nodes[0]
            for node in nodes[1:]:
                dot.edge(prev, node,xlabel=infoset.info_string, style="dashed",color="red",constraint="false",fontcolor="red")
                prev=node

    for abs_infoset,nodes in abstracted_infosets.items():
        if(len(nodes)>1):
            prev=nodes[0]
            for node in nodes[1:]:
                dot.edge(prev, node,xlabel=abs_infoset.info_string, style="dashed",color="blue",constraint="false",fontcolor="blue")
                prev=node

def build_tree(data_ordered,infoset_of):
    actions= [x[1].split("/")[1:] for x in data_ordered]
    #actions=np.array([np.array(xi) for xi in actions])
    children,_=build_subtree(infoset_of,data_ordered[1:],actions[1:],1)
    return Tree("0",children,data_ordered[0],"",Infoset("Nature",0))

def build_subtree(infoset_of,data, actions,id):
    children_action=list(set([x[0] for x in actions]))
    children_action=sorted(children_action)
    #print(actions)
    #print(children_action)
    new_id=id+1
    children=[]
    #print(children_action)
    for action in children_action:
        #print(action)

        data_new=[x for (index, x) in enumerate(data) if actions[index][0]==action]
        #actions_new= [x[1].split("/")[1:] for (index,x) in enumerate(data) if actions[index][0]==action]
        actions_new=[x[1:] for x in actions if x[0]==action]
        #print("Actions_new")
        #print(actions_new)
        #print(actions_new[1:])
        subtree_children,new_id=build_subtree(infoset_of,data_new[1:],actions_new[1:],new_id)


        #print(subtree_children)

        history=data_new[0][1]
        infoset="Not valid"
        if(history in infoset_of):
            infoset=infoset_of[history]
        else:
            infoset="NaN"

        new_node=Tree(str(id),subtree_children,data_new[0],action,infoset)
        id=new_id
        new_id=id+1
        children.append(new_node)

        #history=data_new[0][1]
        #set_infoset(new_node,history,infosets)

    #     data_new=[x for (index, x) in enumerate(data) if actions[index][0]=action)]
    return children,id


def generate_id_infoset_of(infosets):
    infoset_id_of={}
    for infoset,nodes in infosets.items():
        for id in nodes:
            infoset_id_of[id]=infoset

    return infoset_id_of

def read(filename):
    reader = csv.reader(open(filename), delimiter=" ")
    data = list(reader)

    data_polished= [x for x in data if len(x)>0 and x[0]!="#"]
    data_nodes= [x for x in data_polished if x[0]=="node"]
    data_info=[x for x in data_polished if x[0]=="infoset"]

    data_ordered=sorted(data_nodes, key=lambda tuple: tuple[1])

    #for row in data_ordered:
    #    print(row)

    return data_ordered,data_info

if __name__ == '__main__':
    (data_ordered, data_info) =read("testinput.txt")

    actions=set(["P1:c","P1:r","P1:f","P2:c","P2:r","P2:f"])

    infoset_of={}
    for infoset in data_info:
        infoset[0]=Infoset(infoset[1],str(infoset_id))
        infoset_id+=1
        for node in infoset[3:]:
            infoset_of[node]=infoset[0]
    #A questo punto infoset_of contiene le reference agli infoset di tutti e soli i nodi con infoset da infoset_input

    #Questo genera l'albero e assegna degli information set ai nodi per cui ancora manca(quelli che sono singoli)
    tree=build_tree(data_ordered,infoset_of)


    #Costruisce un dizionario che per ogni Infoset ritorna la lista di id di nodi
    infosets={}
    tree.fill_infoset_dictionary(infosets,Infoset("0","0"))

    dot = Graph(comment='My game')
    tree.build_dot(dot,"Begin");


    sequence_table={}
    tree.fill_sequence_form(sequence_table,{"1":"","2":""},1.0,True,"-")
    # for sequence_1,cells in sequence_table.items():
    #     print(sequence_1)
    #     print(cells)
    #     print("")

    #Costruisce una struttura come infoset_of, ma che invece delle stringhe di sequenza ha gli id di nodo
    infoset_id_of=generate_id_infoset_of(infosets)

    #A questo punto:
    #infoset_id_of contiene un dizionario che, dato un id di nodo, restituisce un oggetto Infoset
    #infosets contiene un dizionario che, dato un oggetto Infoset, restituisce una lista di id di nodi
    #infoset_of contiene un dizionario che, data una stringa di sequenza di gioco, restituisce un infoset
    #esempio '/C:JQ/P1:c/P2:r': <__main__.Infoset (...)>


    fake_infosets={}
    fake_id_of={}
    gen_infoset_clusters(actions,infoset_id_of,fake_infosets,fake_id_of,tree.children)

    display="abstract"
    if(display=="true"):
        add_infoset_edges(dot,infosets,{})
    elif(display=="abstract"):
        add_infoset_edges(dot,{},fake_infosets)
    else:
        add_infoset_edges(dot,infosets,fake_infosets)

    dot.render('test-output/round-table.gv', view=False)
