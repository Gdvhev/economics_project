import csv
from graphviz import *
import numpy as np

class Tree:
    def __init__(self, node_id,children,line,action_label):
        self.children=children
        self.node_id=node_id
        self.line=line
        self.action_label=action_label
    def build_dot(self,dot,father_id):
        #dot.node(self.node_id,self.node_id+" Player "+str(self.player_id))
        #player_id="Nature" if (self.line[2]=="chance") else ("Player "+self.line[3])
        if(self.line[2]=="chance"):#Nature
            dot.node(self.node_id,self.node_id+" Nature\n "+str(self.line[4:]))
        elif(self.line[2]=="leaf"):#Terminal Node
            dot.node(self.node_id,self.node_id+" Terminal\n trace: "+self.line[1]+"\n "+str(self.line[3:]))
        else: #Player node
            player_id="Player "+self.line[3]
            dot.node(self.node_id,self.node_id+" "+player_id+"\n "+self.line[1]+"\n "+str(self.line[4:]))
        #dot.node(self.node_id,self.node_id+" "+player_id+str(self.line))
        dot.edge(father_id, self.node_id,label=self.action_label)
        for child in self.children:
            child.build_dot(dot,self.node_id)

def build_tree(data_ordered):
    actions= [x[1].split("/")[1:] for x in data_ordered]
    #actions=np.array([np.array(xi) for xi in actions])
    children,_=build_subtree(data_ordered[1:],actions[1:],1)
    return Tree("0",children,data_ordered[0],"")

def build_subtree(data, actions,id):
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
        subtree_children,new_id=build_subtree(data_new[1:],actions_new[1:],new_id)

        #print(subtree_children)
        new_node=Tree(str(id),subtree_children,data_new[0],action)
        id=new_id
        new_id=id+1
        children.append(new_node)
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

    tree=build_tree(data_ordered)
    dot = Graph(comment='The Round Table')
    tree.build_dot(dot,"Begin");
    dot.render('test-output/round-table.gv', view=False)
