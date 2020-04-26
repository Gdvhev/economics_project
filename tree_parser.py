import csv
from graphviz import *
import numpy as np
from sklearn.cluster import *
import threading
import time

class AtomicCounter:
    def __init__(self, initial=0):
        """Initialize a new atomic counter to given initial value (default 0)."""
        self.value = initial
        self._lock = threading.Lock()

    def increment(self, num=1):
        """Atomically increment the counter by num (default 1) and return the
        new value.
        """
        with self._lock:
            self.value += num
            return self.value

infoset_id=AtomicCounter(-1)
def gen_infoset(dict,player):
    global infoset_id
    i=0
    id=str(infoset_id.increment())
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
        self.strategy={}
        self.next_strategy={}
        self.actions=set()

class Tree:
    """Struttura ricorsiva che rappresenta un nodo dell'albero
        Contiene informazioni sia degli information set veri e anche astratti
    """
    def __init__(self, node_id,children,line,action_label,infoset):
        self.children=children
        self.node_id=node_id
        self.line=line
        self.action_label=action_label
        self.infoset=infoset
        self.action_infoset_label=""
        self.abstracted_infoset=""
        self.abstract_action_infoset_label=""

    def isTerminal(self):
        return self.line[2]=="leaf"

    def isNature(self):
        return self.line[2]=="chance"

    def build_dot(self,dot,father_id,level):
        """ Riempe l'oggetto dot per la parte grafica"""
        #Decommentare per limitare la dimensione dell'output grafico
        #if(level>5):
        #    return

        label=self.node_id
        if(self.isNature()):
            label=label+" Nature\n "+str(self.line[4:])
        elif(self.isTerminal()):
            label=label+" Terminal\n trace: "+self.line[1]+"\n "+str(self.line[3:])
        else: #Player node
            player_id="Player "+self.line[3]
            label=label+" infoset:"+self.infoset.info_string+" "+self.infoset.id+ " "+player_id+"\n "+self.line[1]+"\n "+str(self.line[4:])

        #Crea un nodo grafico
        dot.node(self.node_id,label)

        #Crea il link al padre grafico
        dot.edge(father_id, self.node_id,label=(self.action_label+self.action_infoset_label))

        #Ripeti sui figli
        for child in self.children:
            child.build_dot(dot,self.node_id,level+1)

    def fill_infoset_dictionary(self,dict,id_dic,father_infoset):
        """ Riempie il dizionario degli infoset"""
        player_id="P"
        id_dic[self.node_id]=self
        if(not self.isTerminal()):#Terminali non hanno information set
            if(not self.isNature()):
                player_id=self.line[3]
                self.player_id=self.line[3]
            else:
                player_id="N"

            if(self.infoset=="NaN"):#Se non ancora definito crealo
                self.infoset=gen_infoset(dict,player_id)
                dict[self.infoset]=[self.node_id]
            elif(self.infoset in dict):#Se definito in precedenza aggiungi alla lista questo nodo
                dict[self.infoset].append(self.node_id)
            else:#Se non definito in precedenza crea la lista con solo questo nodo
                dict[self.infoset]=[self.node_id]

        #Ripeti
        for child in self.children:
            child.fill_infoset_dictionary(dict,id_dic,self.infoset)

        #Nessuno dovrebbe avere questo
        if(father_infoset=="NaN"):
            print(self.line)

        #Questo assegna le label alle azioni in base all'infoset del padre
        #esempio L1 R1 vs L2 R2
        self.action_infoset_label=str(father_infoset.id)

    def fill_sequence_form(self,seq_dic,player_history,probability,natureson,father_player):
        """Riempie la tabella della sequence form, non più usata, ignorate"""
        if(not natureson):
            old=player_history[father_player]

            player_history[father_player]=player_history[father_player]+ self.action_label

        if(not self.isNature() and not self.isTerminal()):
            #Player node
            player_id=self.line[3]
            for child in self.children:
                child.fill_sequence_form(seq_dic,player_history,probability,False,player_id)


        elif(self.isTerminal()):
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
        """calcola il vettore dei nodi terminali raggiungibili da self"""
        if(self.isTerminal()):
            out_vector.append(calc_utility(self))
        else:
            for child in self.children:
                child.calculate_outcome_vector(out_vector)
        return out_vector

def get_grandsons(children_list,skip_nature):
    """Prende una lista di children e ritorna la concatenazione dei loro figli
       Salta i nodi natura e ritorna i loro rispettivi figli
    """
    out=[]
    for child in children_list:
        grandsons=[]
        #out+=child.children
        for grandson in child.children:
            if(grandson.isNature()):
                grandsons+=grandson.children
            else:
                grandsons.append(grandson)
        out+=grandsons
    return out

def cluster_and_recur(actions,infoset_of,fake_infosets,fake_id_of,children,vectors,children_infosets):
    """Usa i vettori dati(assunti lunghi uguali) e applica clustering per trovare gli information set astratti"""

    #Altrimenti non rileva la variabile globale
    global infoset_id
    if(len(vectors)==0):
        return
    if(len(vectors)==1):#Se ho solo un vettore è ovviamente in cluster da solo
        #print("Skipping %s as lone vector"%vectors)
        labels=[0]
    else:
        #Dobbiamo ancora trovare quale sia l'algoritmo migliore, kMeans per ora sembra andare

        #magic number 0.27
        eps=0.27*len(vectors)#TODO valore
        clustering = KMeans(n_clusters=2).fit(vectors)
        #clustering=DBSCAN(eps=eps, min_samples=2).fit(vectors)
        #print(vectors)
        #clustering= OPTICS(min_samples=1,metric='manhattan').fit(vectors)
        labels=clustering.labels_

    #print("Cluster targets: %s" %labels)

    #info_store contiene gli abstracted information set eventualmente creati
    fake_info_store={}
    outlier_counter=-2

    #Per ogni vettore(information set reale)
    for index,obj in enumerate(labels):
        if(obj==-1):#Se outlier allora creiamo un cluster finto
            obj=outlier_counter
            outlier_counter-=1

        #Se questo cluster ha già un infoset astratto usalo, altrimenti crealo
        if(not obj in fake_info_store):
            fake_infoset=Infoset("",str(infoset_id.increment(1)))
            fake_info_store[obj]=fake_infoset
            fake_infosets[fake_infoset]=[]

        else:
            fake_infoset=fake_info_store[obj]

        #Assegna l'information set astratto all'information set reale
        children_infosets[index].abstracted_infoset=fake_infoset

        #Aggiungi nella stringa di descrizione l'information set reale
        fake_infoset.info_string=fake_infoset.info_string+"+"+children_infosets[index].info_string


    for child in children:
        #Assegna a tutti i figli l'information set astratto corrispondente
        if(child.infoset.abstracted_infoset!=""):
            child.abstracted_infoset=child.infoset.abstracted_infoset
            child.abstract_action_infoset_label=child.infoset.abstracted_infoset.id
            fake_id_of[child.node_id]=child.abstracted_infoset
            fake_infosets[child.abstracted_infoset].append(child.node_id)



    abstracted_infosets=list(fake_info_store.values())

    #Vecchio codice, lo lascio con l'assert per fermare bug, per il momento non scatta mai
    unused_infosets=[infoset for infoset in children_infosets if infoset.abstracted_infoset==""]
    assert(len(unused_infosets)==0)
    recur_infosets=unused_infosets +abstracted_infosets

    #Lo store contiene, per ogni information set astratto e per ogni azione, una lista di figli su cui ricorrere
    #Questo ci permette di fare clustering solo tra figli dello stesso information set e dalla stessa azione
    #Non dovendo quindi controllare la sequenza per partizionare i vettori, ma solo la lunghezza
    children_store={ i : {j:[] for j in actions} for i in recur_infosets }

    #Ripeti per ogni gruppo di figli di ogni information set astratto o che non è stato astratto
    for child in children:
        cinfoset=child.infoset

        for action in actions:

            #Estrai tutti i figli degli information set attuali(escludendo terminali)
            grandsons=[grandson for grandson in child.children if not grandson.isTerminal() and grandson.action_label==action ]

            if(cinfoset.abstracted_infoset==""):
                #Anche qua vecchio codice che non dovrebbe scattare
                children_store[cinfoset][action]=children_store[cinfoset][action]+grandsons
            else:
                if(not cinfoset.abstracted_infoset in abstracted_infosets):
                    #Print di debug in caso manchi l'information set
                    print(cinfoset in unused_infosets)
                    print(cinfoset.info_string)
                    print(cinfoset.abstracted_infoset.info_string)
                    print(cinfoset.abstracted_infoset)
                    #Error if this branch is taken

                children_store[cinfoset.abstracted_infoset][action]=children_store[cinfoset.abstracted_infoset][action]+grandsons

    #print("----------Children store is----------")
    #print(children_store)
    #print("----------------------------------")

    #Per ogni partizione in children_store
    for _,store in children_store.items():
        print()
        for action,children_list in store.items():
            #print(action)
            #print(children_list)

            #Salta un livello(i figli dei figli sono del giocatore sbagliato, noi vogliamo
            # i figli dei figli dei figli, che sono di nuovo del giocatore attuale
            grandson_list=get_grandsons(children_list,True)

            #Filtra i terminali
            grandson_list=[grandson for grandson in grandson_list if not grandson.isTerminal()]

            #print(grandson_list)
            #print("--------------------------------")

            gen_infoset_clusters(actions,infoset_of,fake_infosets,fake_id_of,grandson_list)

def gen_infoset_clusters(actions,infoset_of,fake_infosets,fake_id_of,children):
    """ Prende in input gli information set astratti e reali e una lista di children, e cerca di fare clustering quando
        Si trova una corrispondenza nelle strutture"""
    if(len(children)==0):
        return
    children_infosets=[]
    #print("----------Children is----------")
    #print(children)
    #print("------------------------------")

    #Estrai gli information sets di tutti i figli
    for child in children:
        if(infoset_of[child.node_id] not in children_infosets):
            children_infosets.append(infoset_of[child.node_id])

    #print(children_infosets)

    #Matrici che per ogni struttura(lunghezza del vettore degli outcome) ci danno:
    outcome_matrix={}#i vettori, un vettore per ogni information set reale
    relevant_matrix={}#i children che hanno generato questi vettori
    relevant_infosets_matrix={}#gli information set che hanno generato questi

    #Potrebbe essere ottimizzato, ma tanto il vero tempo viene preso dal clustering
    for infoset in children_infosets:
        vector=[]
        relevant_children=[]

        #Per ogni children di questo information set concatena i vettori degli output raggiungibili
        for child in children:
            if(infoset == infoset_of[child.node_id]):
                cv =child.calculate_outcome_vector([])
                vector=vector+cv
                relevant_children.append(child)

        #Metti questo vettore con i suoi simili
        if(len(vector) not in outcome_matrix):
            outcome_matrix[len(vector)]=[]
            relevant_matrix[len(vector)]=[]
            relevant_infosets_matrix[len(vector)]=[]
        outcome_matrix[len(vector)].append(vector)
        relevant_matrix[len(vector)]+=(relevant_children)
        relevant_infosets_matrix[len(vector)].append(infoset)


    #Per ogni gruppo di vettori fai clustering
    for size,vectors in outcome_matrix.items():
        #print(vectors)
        cluster_and_recur(actions,infoset_of,fake_infosets,fake_id_of,relevant_matrix[size],vectors,relevant_infosets_matrix[size])



def add_infoset_edges(dot,infosets,abstracted_infosets):
    """Aggiunge al dot gli archi relativi agli infoset reali e astratti """
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

def build_tree(data_ordered,infoset_of,action_set):
    """Costruisce l'albero """

    #Actions sono le azioni di entrambi i giocatori per ogni riga
    #actions[i] è una lista di azioni fatte per raggiungere il nodo i
    actions= [x[1].split("/")[1:] for x in data_ordered]

    #Chiamata ricorsiva che Costruisce la lista di figli
    children,_=build_subtree(infoset_of,data_ordered[1:],actions[1:],1,action_set)

    #Crea il nodo radice con la lista precedentemente creata
    return Tree("0",children,data_ordered[0],"",Infoset("Nature",0))

def build_subtree(infoset_of,data, actions,id,action_set):
    """Crea la lista di figli del nodo dato, creando tutti i sottoalberi ricorsivamente"""

    #Cose, non rilevanti per il resto del codice
    children_action=list(set([x[0] for x in actions]))
    children_action=sorted(children_action)

    new_id=id+1
    children=[]

    for action in children_action:

        if action not in action_set:
            action_set.add(action)
        data_new=[x for (index, x) in enumerate(data) if actions[index][0]==action]

        actions_new=[x[1:] for x in actions if x[0]==action]

        subtree_children,new_id=build_subtree(infoset_of,data_new[1:],actions_new[1:],new_id,action_set)

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

    return children,id


def generate_id_infoset_of(infosets):
    """ Genera un dizionario che per ogni id di nodo ci da l'Infoset"""
    infoset_id_of={}
    for infoset,nodes in infosets.items():
        for id in nodes:
            infoset_id_of[id]=infoset

    return infoset_id_of

def read(filename):
    """ Apre il csv e crea le strutture dati """
    reader = csv.reader(open(filename), delimiter=" ")

    #data sono le righe lette senza elaborazione
    data = list(reader)

    #togli righe vuote e commenti
    data_polished= [x for x in data if len(x)>0 and x[0]!="#"]

    #separa nodi e information set
    data_nodes= [x for x in data_polished if x[0]=="node"]
    data_info=[x for x in data_polished if x[0]=="infoset"]

    #ordina in base alla sequenza lessicograficamente
    data_ordered=sorted(data_nodes, key=lambda tuple: tuple[1])

    return data_ordered,data_info


def add_abstracted_actions(infosets,id_dic):
    for infoset,children_id in infosets.items():
        assert(len(children_id)>0)
        champion=id_dic[children_id[0]]
        for child in champion.children:
            infoset.actions.add(child.action_label)

def parse_and_abstract(filename):
    start_time = time.time()
    (data_ordered, data_info) =read(filename)

    #Actions conterrà tutte le azione mai incontrate
    actions=set()

    infoset_of={}
    for infoset in data_info:
        infoset[0]=Infoset(infoset[1],str(infoset_id.increment()))
        for node in infoset[3:]:
            infoset_of[node]=infoset[0]
    #A questo punto infoset_of contiene le reference agli infoset di tutti e soli i nodi con infoset da infoset_input

    #Questo genera l'albero e assegna degli information set ai nodi per cui ancora manca(quelli che sono singoli)
    tree=build_tree(data_ordered,infoset_of,actions)


    #Costruisce un dizionario che per ogni Infoset ritorna la lista di id di nodi
    infosets={}
    id_dic={}
    tree.fill_infoset_dictionary(infosets,id_dic,Infoset("0","0"))

    #Inizializza il grafico, svg è l'unico che permette di usare gli input grandi
    dot = Graph(comment='My game',format='svg')
    tree.build_dot(dot,"Begin",0);

    #Vecchia sequence table non più usata, lasciata per sicurezza
    #sequence_table={}
    #tree.fill_sequence_form(sequence_table,{"1":"","2":""},1.0,True,"-")
    # for sequence_1,cells in sequence_table.items():
    #     print(sequence_1)
    #     print(cells)
    #     print("")


    #Costruisce una struttura come infoset_of, ma che invece delle stringhe di sequenza ha gli id di nodo
    infoset_id_of=generate_id_infoset_of(infosets)

    #A questo punto:
    #infoset_id_of contiene un dizionario che, dato un id di nodo, restituisce un oggetto Infoset
    #infosets contiene un dizionario che, dato un oggetto Infoset, restituisce una lista di id di nodi
    #infoset_of contiene un dizionario che, data una stringa di sequenza di gioco, restituisce un Infoset
    #esempio '/C:JQ/P1:c/P2:r': <__main__.Infoset (...)>


    #Fake_ sono gli oggetti che contengono gli information set astratti
    fake_infosets={}
    fake_id_of={}

    #Crea i cluster e astrae il gioco, riempiendo le variabili relative all'astrazione
    gen_infoset_clusters(actions,infoset_id_of,fake_infosets,fake_id_of,tree.children)
    gen_infoset_clusters(actions,infoset_id_of,fake_infosets,fake_id_of,get_grandsons(tree.children,False))


    root_abstract_infoset=Infoset("0",str(infoset_id.increment(1)))
    fake_infosets[root_abstract_infoset]=["0"]
    fake_id_of["0"]=root_abstract_infoset
    tree.abstracted_infoset=root_abstract_infoset

    #Il multithreading funziona ma per qualche motivo rallenta
    # thread1=threading.Thread(target=gen_infoset_clusters, args=(actions,infoset_id_of,fake_infosets,fake_id_of,tree.children))
    # thread2=threading.Thread(target=gen_infoset_clusters, args=(actions,infoset_id_of,fake_infosets,fake_id_of,get_grandsons(tree.children)))
    # thread2.start()
    # thread1.start()
    # thread1.join()
    # thread1.join()


    display="abstract"
    if(display=="true"):#solo infoset reali
        add_infoset_edges(dot,infosets,{})
    elif(display=="abstract"):#solo astratti
        add_infoset_edges(dot,{},fake_infosets)
    else:#clusterfuck
        add_infoset_edges(dot,infosets,fake_infosets)

    print(infosets)
    print("---------------------")
    print(fake_infosets)
    print("Fake infoset size %d"% len(fake_infosets))
    print("Real infoset size %d"% len(infosets))

    add_abstracted_actions(fake_infosets,id_dic)

    dot.render('test-output/round-table.gv', view=False)
    print("--- %s seconds ---" % (time.time() - start_time))
    return tree,id_dic,infosets,infoset_of,infoset_id_of,fake_infosets,fake_id_of

if __name__ == '__main__':
    parse_and_abstract("testinput.txt")
