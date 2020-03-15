import csv
from graphviz import *
import numpy as np

class Tree:
    def __init__(self, node_id,player_id,children):
        self.children=children
        self.player_id=player_id
        self.node_id=node_id

    def build_dot(self,dot,father_id):
        dot.node(self.node_id,"Player "+str(self.player_id))
        dot.edge(father_id, self.node_id, constraint='false')
        for child in self.children:
            child.build_dot(dot,self.node_id)

def build_tree(data_ordered):
    actions= [x[1].split("/")[1:] for x in data_ordered]
    #actions=np.array([np.array(xi) for xi in actions])
    return Tree("0", "N",build_subtree(data_ordered[1:],actions[1:]))

def build_subtree(data, actions):
    #print("ACTIONS")
    children_action=list(set([x[0] for x in actions]))
    children_action=sorted(children_action)
    print(actions)
    print("CIAO")
    print(children_action)

    # children=[]
    # for action in children_action:
    #     for (index, row) in enumerate(data):
    #
    #     data_new=[x for (index, x) in enumerate(data) if actions[index][0]=action)]

def read(filename):
    reader = csv.reader(open(filename), delimiter=" ")
    data = list(reader)

    data_polished= [x for x in data if len(x)>0 and x[0]!="#"]
    data_nodes= [x for x in data_polished if x[0]=="node"]
    data_info=[x for x in data_polished if x[0]=="infoset"]

    data_ordered=sorted(data_nodes, key=lambda tuple: tuple[1])

    for row in data_ordered:
        print(row)

    return data_ordered,data_info

if __name__ == '__main__':
    (data_ordered, data_info) =read("testinput.txt")

    tree=build_tree(data_ordered)
    dot = Digraph(comment='The Round Table')
    tree.build_dot(dot,"A");
    dot.render('test-output/round-table.gv', view=True)
