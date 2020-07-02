import numpy as np
from tree_parser import *
from functools import reduce
import random
from decimal import *
class Context:
    def __init__(self, infosets,infoset_id_of,id_dic):
        self.infosets=infosets
        self.infoset_id_of=infoset_id_of
        self.id_dic=id_dic
        self.tot=0.0

    def init_matrices(self,resetRegret):
        self.cumulative_regret={infoset:{action:0.0 for action in infoset.actions} for infoset in self.infosets.keys()}
        self.cumulative_strategy={infoset:{action:0.0 for action in infoset.actions} for infoset in self.infosets.keys()}



        if(resetRegret):
            self.R_T={infoset: {action:0.0 for action in infoset.actions} for infoset in self.infosets.keys()}
            self.tot=0.0

    def resetRegret(self):
        self.R_T={infoset: {action:0.0 for action in infoset.actions} for infoset in self.infosets.keys()}
        #print(self.cumulative_regret)

def gen_strats(filename,n_iterations):
    tree,id_dic,infosets,_,infoset_id_of,fake_infosets,fake_id_of=parse_and_abstract(filename,False)
    # print("--------------------------------------------------------------_")
    # print(tree.children[0].infoset.actions)
    # print(tree.children[0].infoset.abstracted_infoset.actions)
    for infoset in infosets.keys():
        if(infoset.abstracted_infoset!=""):
            infoset.actions=infoset.abstracted_infoset.actions
    start_time=time.time()
    # n_iterations = 200000
    context=Context(fake_infosets,fake_id_of,id_dic)

    context.init_matrices(True)
    prepare_strategy(fake_infosets,id_dic)

    for i in range(0,n_iterations):
        val=do_iteration(tree,i,context,fake_infosets,[],0)
        # if(val<=(-0.9/18) and val>=(-1.1/18)):
        #     break

    print("Final Strategy:")
    for infoset in fake_infosets:
        print("%s : %s"%(infoset.info_string,infoset.strategy))

    print("Average Strategy:")
    for infoset in fake_infosets:
        get_average_strategy(infoset,context)
        clean_strategy(infoset,context,2)
        infoset.strategy=infoset.next_strategy#disable to disable averaging
        print("%s : %s"%(infoset.info_string,infoset.next_strategy))
    print("Generating diagram")
    apply_edges_to_diagram(tree,infosets,fake_infosets,id_dic,fake_id_of,False)
    print("--- Solving took %s seconds ---" % (time.time() - start_time))

    back_map(infosets)

    output_strategy("strategy.txt",infosets,infoset_id_of,val,len(infosets),len(fake_infosets))
    return tree,id_dic,infosets,infoset_id_of,val,fake_infosets


def do_iteration(tree,i,context,fake_infosets,subgame,sub_player):
    subgame=[x.node_id for x in subgame]
    #context.init_matrices(False)
    context.resetRegret()
    #val=apply_cfr(fake_id_of["0"],i,fake_infosets,fake_id_of,id_dic,player,[1,1])
    sub1=subgame if sub_player==1 else []
    val1=cfr2(tree,0,i,1.0,1.0,context,sub1)
    #print("\n----------Moving to player 2-------\n")
    #
    #print("Subgame %s"%subgame)
    sub2= subgame if sub_player==2 else []
    val2=cfr2(tree,1,i,1.0,1.0,context,sub2)
    context.tot+=val1
    #print(list(context.cumulative_regret.values())[0])
    average_val=context.tot/(i+1)
    print("Result %f of iteration %d is %f %f" %(average_val,i,val1,val2))
    for infoset in fake_infosets:
        #print(infoset.strategy)
        #infoset.strategy=infoset.next_strategy.copy()
        for action in infoset.next_strategy.keys():
            infoset.strategy[action]=infoset.next_strategy[action]
        infoset.next_strategy={}

        #print(infoset.info_string)
        #print(infoset.strategy)
        #print("%s : %s"%(infoset.info_string,infoset.strategy))
    return average_val

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

def calc_expected(tree,player):
    if(tree.isTerminal()):
        return handle_terminal(tree,player)
    elif(tree.isNature()):
        accum=0.0
        num_c=len(tree.children)
        probs=tree.line[4:]
        prob_func=lambda i:float(probs[i].split("=")[1])/num_c
        for i,child in enumerate(tree.children):
            probability=float(probs[i].split("=")[1])/num_c
            accum+= calc_expected(tree,player)
        return accum
    else:
        accum=0.0
        for child in tree.children:
            accum+=calc_expected(child,player)*tree.infoset.strategy[child.action_label]
        return accum

def cfr2(tree,player,iteration,p1,p2,context,subgame):
    if(len(subgame)>0 and tree.node_id not in subgame):
        #print("Skipping %s %s"%(tree,tree.node_id))
        return calc_expected(tree,player)
    #print("Handling %s p1=%f p2=%f" % (tree.line[1],p1,p2))
    if(tree.isTerminal()):
        return handle_terminal(tree,player)

    if(tree.isNature()):
        accum=0.0
        num_c=len(tree.children)
        probs=tree.line[4:]
        prob_func=lambda i:float(probs[i].split("=")[1])/num_c

        #No monte carlo
        for i,child in enumerate(tree.children):
           probability=float(probs[i].split("=")[1])/num_c
           accum+= probability*cfr2(child,player,iteration,p1*probability,p2*probability,context,subgame)
        #
        #Monte carlo
        # selected=random.randint(0,len(tree.children)-1)
        # accum+=cfr2(tree.children[selected],player,iteration,p1,p2,context,subgame)
        return accum

    if(tree.node_id not in context.infoset_id_of):
        print(tree.line)
    infoset=context.infoset_id_of[tree.node_id]

    # print(tree.node_id)
    # print(tree.children)
    # print([x.strategy for x in context.infoset_id_of.values()])

    #print(tree.line[1])
    #print(infoset.info_string)
    value=0.0

    value_actions={action: 0 for action in infoset.actions}
    #print(value_actions)

    #for action in infoset.actions:
    #    for child in tree.children:
    for child in tree.children:
        action=child.action_label
        if(tree.player_id=="1"):
            if(not action in infoset.strategy):
                print("Error %s %s %s"%(child.node_id,infoset.strategy,tree.node_id))
            new_p1=p1*infoset.strategy[action]
            value_actions[action]=cfr2(child , player,iteration, new_p1,p2,context,subgame)
        else:
            new_p2=p2*infoset.strategy[action]
            value_actions[action]=cfr2(child , player,iteration, p1,new_p2,context,subgame)

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
    cumulative_regret=context.cumulative_regret[infoset]
    context.R_T[infoset]={action: v+cumulative_regret[action] for action,v in context.R_T[infoset].items()}

    rt=context.R_T[infoset]
    regret_sum=reduce(lambda x, a :x + (rt[a] if rt[a]>0 else 0.0), rt, 0.0)
    for action in infoset.actions:
        if(regret_sum>0):
            #print("HELLOOOOO %s"%action)
            if(context.R_T[infoset][action]>0):
                infoset.next_strategy[action]=context.R_T[infoset][action]/regret_sum
            else:
                infoset.next_strategy[action]=0.0
            #print(infoset.next_strategy[action])
            #print("%d %d"%(context.cumulative_regret[infoset][action],regret_sum))

        else:
            infoset.next_strategy[action]= 1.0/ len(infoset.actions)

    #print("CHIAMATO------------------------------------------------%s"%infoset.next_strategy)

def get_average_strategy(infoset,context):
    rt=context.cumulative_strategy[infoset]
    regret_sum=reduce(lambda x, a :x + (rt[a] if rt[a]>0 else 0.0), rt, 0.0)
    for action in infoset.actions:
        if(regret_sum>0):
            #print("HELLOOOOO %s"%action)
            if(context.cumulative_strategy[infoset][action]>0):
                infoset.next_strategy[action]=context.cumulative_strategy[infoset][action]/regret_sum
            else:
                infoset.next_strategy[action]=0.0
        else:
            infoset.next_strategy[action]= 1.0/ len(infoset.actions)

def clean_strategy(infoset,context,cutoff):
    acc=0.0
    for action in infoset.actions:
        infoset.next_strategy[action]=round(infoset.next_strategy[action], cutoff)
        acc+=infoset.next_strategy[action]

    acc=round(acc,cutoff)
    if(acc!=1.0):
        print("Warning, non 1-sum probability vector %f :%s"%(acc,infoset.next_strategy))
        diff=round(1.0-acc,cutoff)
        if diff>0:#Missing probability
            for action in infoset.actions:
                if infoset.next_strategy[action]+diff<=1.0:
                    infoset.next_strategy[action]=round(infoset.next_strategy[action]+diff,cutoff)
                    diff=0.0
                    break
                else:
                    diff-=(1.0-infoset.next_strategy[action])
                    assert(diff>=0)
                    infoset.next_strategy[action]=1.0
        else:#Eccess probability
            diff=-diff
            for action in infoset.actions:
                if infoset.next_strategy[action]-diff>=0.0:
                    infoset.next_strategy[action]=round(infoset.next_strategy[action]-diff,cutoff)
                    diff=0.0
                    break
                else:
                    diff-=infoset.next_strategy[action]
                    assert(diff>=0)
                    infoset.next_strategy[action]=0.0
        acc=0.0
        for action in infoset.actions:
            acc+=infoset.next_strategy[action]
        print("Corrected to %f :%s"%(acc,infoset.next_strategy))
        acc=round(acc,cutoff)
        assert(acc==1.0)


def handle_terminal(node,player):
    assert(node.isTerminal())
    index=4
    if(player==1):
        index=5
    utility=float(str(node.line[index]).split("=")[1])
    return utility

def back_map(infosets):
    for infoset in infosets.keys():
        if(infoset.abstracted_infoset!=""):
            infoset.strategy=infoset.abstracted_infoset.strategy

def output_strategy(filename,infosets,infoset_id_of,val,infon,fakeinfon):
    f = open(filename,"w")
    #del infosets[infoset_id_of["0"]]
    f.write("#Autogenerated strategy for the Franzini,Gianotti,Lundardon,Disarò group of the ec course\n")
    f.write("#%f, Infosets original %d, abstracted %d\n"%(val,infon,fakeinfon))
    #print(infosets)
    for infoset in infosets:
        actions_string=""
        if(len(infoset.strategy)==0):
            #print("Skipping %s",infoset.info_string)
            continue
        for action,value in infoset.strategy.items():
            actions_string+=action.split(":")[1]+"="+str(value)+" "
        f.write("infoset %s strategies %s\n"%(infoset.info_string,actions_string))

if __name__ == "__main__":
    gen_strats("testinput.txt",1000)
