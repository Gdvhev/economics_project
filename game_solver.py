import numpy as np
from tree_parser import *

class Context:
    def __init__(self, infosets,infoset_id_of,id_dic):
        self.infosets=infosets
        self.infoset_id_of=infoset_id_of
        self.id_dic=id_dic

    def init_matrices(self,resetRegret):
        self.cumulative_regret={infoset:{action:0 for action in infoset.actions} for infoset in self.infosets.keys()}

        self.cumulative_strategy={infoset:{action:0 for action in infoset.actions} for infoset in self.infosets.keys()}


        if(resetRegret):
            self.R_T={infoset: {action:0 for action in infoset.actions} for infoset in self.infosets.keys()}
        print(self.cumulative_regret)

def main():
    tree,id_dic,_,_,_,fake_infosets,fake_id_of=parse_and_abstract("testinput.txt")
    n_iterations = 2
    expected_game_value = 0
    context=Context(fake_infosets,fake_id_of,id_dic)

    context.init_matrices(True)
    prepare_strategy(fake_infosets,id_dic)
    for i in range(0,n_iterations):
        context.init_matrices(False)
        player=0
        #val=apply_cfr(fake_id_of["0"],i,fake_infosets,fake_id_of,id_dic,player,[1,1])
        val1=cfr2(tree,0,i,1,1,context)
        print("\n----------Moving to player 2-------\n")
        val2=cfr2(tree,1,i,1,1,context)
        print("Result of iteration %d is %d %d" %(i,val1,val2))

        for infoset in fake_infosets:
            infoset.strategy=infoset.next_strategy
            infoset.next_strategy={}
            print(infoset.info_string)
            print(infoset.strategy)

def prepare_strategy(infosets,id_dic):
    for infoset,nodes in infosets.items():

        nodes_obj=[id_dic[x] for x in nodes]
        if(len(nodes_obj)==0):
            continue
        count=len(nodes_obj[0].children)
        for action in infoset.actions:
            infoset.strategy[action]= 1.0/count

        #print(infoset.strategy)
        #Manca la natura


# def apply_cfr(current_infoset,iteration,infosets,infoset_id_of,id_dic,player,probability_vector):
#     print("------")
#     print(probability_vector)
#     nodes_ids=infosets[current_infoset]
#     nodes_obj=[id_dic[x] for x in nodes_ids]
#     if(len(nodes_ids)==1):
#         if(nodes_obj[0].isTerminal()): #Not alive anymore
#             return calc_utility(nodes_obj[0],probability)
#
#         if(nodes_obj[0].isNature()):
#             member_children=nodes_obj[0].children
#             return recur_cfr(current_infoset,iteration,infosets,infoset_id_of,id_dic,player,probability_vector,member_children,True)
#
#
#     player=(player+1)%2
#     value=0
#     action_values=list(current_infoset.actions)
#     print("At infoset %s player %d and probability %f"% (current_infoset.info_string,player,probability_vector[player]))
#     print(action_values)
#
#     member_children=[]
#     terminal_children=[]
#     for member in nodes_obj:
#         member_children+=member.children
#
#
#     accum=0
#     terminal_children=[child for child in member_children if child.isTerminal()]
#     member_children=[child for child in member_children if not child.isTerminal()]
#
#     for terminal_child in terminal_children:
#         handle_terminal(terminal_child,player)
#
#     accum=recur_cfr(current_infoset,iteration,infosets,infoset_id_of,id_dic,player,probability_vector,member_children,False)
#
#     return accum

# def recur_cfr(current_infoset,iteration,infosets,infoset_id_of,id_dic,player,probability_vector,member_children,isNature):
#     if(isNature):
#         player=(player+1)%2
#     children_infosets={}
#     for child in member_children:
#         child_infoset=infoset_id_of[child.node_id]
#         if child_infoset not in children_infosets:
#             children_infosets[child_infoset]=[child.action_label]
#
#     accum=0
#     old_prob=probability_vector.copy()
#     for child_infoset,actions in children_infosets.items():
#         #probability_vector[(player+1)%2]=probability_vector[(player+1)%2]*1#TODO actually use probability
#
#         #TODO giusto prendere un champion??
#         if(isNature):
#             probability_vector=[prob*current_infoset.strategy[actions[0]] for prob in probability_vector]
#         else:
#             probability_vector[player]=probability_vector[player]*current_infoset.strategy[actions[0]]
#
#         accum+=apply_cfr(child_infoset,iteration,infosets,infoset_id_of,id_dic,player,probability_vector)
#
#
#         probability_vector=old_prob.copy()
    #
    # return accum


def cfr2(tree,player,iteration,p1,p2,context):
    print("Handling %s p1=%f p2=%f" % (tree.line[1],p1,p2))
    if(tree.isTerminal()):
        return handle_terminal(tree,player)

    if(tree.isNature()):
        #TODO actually handle natures
        accum=0
        for child in tree.children:
            accum+= cfr2(child,player,iteration,p1,p2,context)
        return accum

    infoset=context.infoset_id_of[tree.node_id]
    #print(tree.line[1])
    #print(infoset.info_string)
    value=0

    value_actions={action: 0 for action in infoset.actions}
    #print(value_actions)

    for action in infoset.actions:
        for child in tree.children:
            if(child.action_label!=action):
                continue
        # for child in tree.children:
        #     if(child.action_label==action):
        #         chosen=child

            if(tree.player_id=="1"):
                new_p1=p1*infoset.strategy[action]
                value_actions[action]=cfr2(child , player,iteration, new_p1,p2,context)
            else:
                new_p2=p2*infoset.strategy[action]
                value_actions[action]=cfr2(child , player,iteration, p1,new_p2,context)

            value+=infoset.strategy[action]*value_actions[action]


    if((tree.player_id=="1" and player==0) or (tree.player_id=="2" and player==1)):
        #print("Entered")
        if(player==0):
            p_mine=p1
            p_other=p2
        else:
            p_mine=p2
            p_other=p1

        for action in infoset.actions:
            context.cumulative_regret[infoset][action]+=p_other*(value_actions[action]-value)

            context.cumulative_strategy[infoset][action] +=p_mine*infoset.strategy[action]

        update_strategy(infoset,context)
    return value

def update_strategy(infoset,context):
    regret_sum=0
    for action in infoset.actions:
        context.R_T[infoset][action]+=context.cumulative_regret[infoset][action]
        if(context.R_T[infoset][action]>0):
            regret_sum+=context.R_T[infoset][action]

    for action in infoset.actions:
        if(regret_sum>0):
            print("HELLOOOOO %s"%action)
            if(context.R_T[infoset][action]>0):
                infoset.next_strategy[action]=context.R_T[infoset][action]/regret_sum
            else:
                infoset.next_strategy[action]=0
            print(infoset.next_strategy[action])
            print("%d %d"%(context.cumulative_regret[infoset][action],regret_sum))

        else:
            infoset.next_strategy[action]= 1.0/ len(infoset.actions)

def handle_terminal(node,player):
    assert(node.isTerminal())
    index=4
    if(player==1):
        index=5
    utility=float(str(node.line[index]).split("=")[1])
    return utility


if __name__ == "__main__":
    main()
