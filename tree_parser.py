import csv
from graphviz import *
import numpy as np


def gen_infoset(dict,player):
    i=0
    while(player+"."+str(i) in dict):
        i=i+1
    return player+"."+str(i)
class Tree:
    def __init__(self, node_id,children,line,action_label,infoset):
        self.children=children
        self.node_id=node_id
        self.line=line
        self.action_label=action_label
        self.infoset=infoset
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
            label=label+" infoset:"+self.infoset+" "+player_id+"\n "+self.line[1]+"\n "+str(self.line[4:])
        #dot.node(self.node_id,self.node_id+" "+player_id+str(self.line))
        dot.node(self.node_id,label)
        dot.edge(father_id, self.node_id,label=self.action_label)
        for child in self.children:
            child.build_dot(dot,self.node_id)

    def set_infoset(self,new_infoset):
        self.infoset=infoset

    def fill_infoset_dictionary(self,dict):
        player_id="P"
        if(self.line[2]!="chance" and self.line[2]!="leaf"):#Nature or Terminal
            player_id=self.line[3]

            if(self.infoset=="NaN"):
                self.infoset=gen_infoset(dict,player_id)
                dict[self.infoset]=[self.node_id]
            elif(self.infoset in dict):
                dict[self.infoset].append(self.node_id)
            else:
                dict[self.infoset]=[self.node_id]

        for child in self.children:
            child.fill_infoset_dictionary(dict)


def add_infoset_edges(dot,infosets):
    for infoset,nodes in infosets.items():
        if(len(nodes)>1):
            prev=nodes[0]
            for node in nodes[1:]:
                dot.edge(prev, node,xlabel=infoset, style="dashed",color="red",constraint="false",fontcolor="red")
                prev=node

def build_tree(data_ordered,infoset_of):
    actions= [x[1].split("/")[1:] for x in data_ordered]
    #actions=np.array([np.array(xi) for xi in actions])
    children,_=build_subtree(infoset_of,data_ordered[1:],actions[1:],1)
    return Tree("0",children,data_ordered[0],"","0.0")

def build_subtree(infoset_of,data, actions,id):
    #print("ACTIONS")
    children_action=list(set([x[0] for x in actions]))
    children_action=sorted(children_action)
    #print(actions)
    #print("CIAO")
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

    # list_of_nodes=[x[3:]for x in data_info]
    # list_of_infosets=[x[1]for x in data_info]
    # info_zip=zip(list_of_infosets,list_of_nodes)
    # infoset_input=dict(info_zip)
    # print(infoset_input)

    infoset_of={}
    for infoset in data_info:
        for node in infoset[3:]:
            infoset_of[node]=infoset[1]
    #print(infoset_of)


    tree=build_tree(data_ordered,infoset_of)

    infosets={}
    tree.fill_infoset_dictionary(infosets)
    print(infosets)

    dot = Graph(comment='My game')
    tree.build_dot(dot,"Begin");
    add_infoset_edges(dot,infosets)

    dot.render('test-output/round-table.gv', view=False)
