# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 19:07:57 2020

@author: Lenovo
"""


import numpy as np

# Number of actions a player can take at a decision node.
_N_ACTIONS_STANDARD = 2
_N_ACTIONS_RAISE = 3
_N_CARDS = 3

def main():

    #WE NEED TO INSERT OUR INFO SETS HERE!
    i_map = {}  # map of information sets
    n_iterations = 10000
    expected_game_value = 0

    for _ in range(n_iterations):
        expected_game_value += cfr(i_map)
        for _, v in i_map.items():
            v.next_strategy()

    expected_game_value /= n_iterations

    display_results(expected_game_value, i_map)
    
    #FUNCTION CFR

def cfr(i_map, history="", card_1=-1, card_2=-1, pr_1=1, pr_2=1, pr_c=1, card_N=-1):

    if is_chance_node(history):
        return chance_util(i_map,history)

    if is_terminal(history) and len(history) < 7:
        return terminal_util_short(history, card_1, card_2)
    
    if is_terminal(history) and len(history) >= 7:
        return terminal_util_full(history, card_1, card_2, card_N)

    n = len(history)
    is_player_1 = n % 2 == 0
    info_set = get_info_set(i_map, card_1 if is_player_1 else card_2, history)

    strategy = info_set.strategy
    if is_player_1:
        info_set.reach_pr += pr_1
    else:
        info_set.reach_pr += pr_2

    # Counterfactual utility per action
    action_utils_standard = np.zeros(_N_ACTIONS_STANDARD)
    action_utils_raise = np.zeros(_N_ACTIONS_RAISE)

    #RAISE CASE: RAISE, CALL AND FOLD  AVAILABLE
    if (history.endswith("r")  and not history.endswith("rr")):
        for i, action in enumerate(["r", "c", "f"]):
            next_history = history + action
            if is_player_1:
               action_utils_raise[i] = -1 * cfr(i_map, next_history, card_1, card_2, pr_1 * strategy[i], pr_2, pr_c)
            else:
               action_utils_raise[i] = -1 * cfr(i_map, next_history,card_1, card_2, pr_1, pr_2 * strategy[i], pr_c)
               
        # Utility of information set.
        util = sum(action_utils_raise * strategy)
        regrets = action_utils_raise - util
        if is_player_1:
           info_set.regret_sum += pr_2 * pr_c * regrets
        else:
           info_set.regret_sum += pr_1 * pr_c * regrets

        return util
            
    
     #STANDARD CASE: ONLY FOLD AND CALL AVAILABLE
    if history.endswith("rr"):
        for i, action in enumerate(["f", "c"]):
            next_history = history + action
            if is_player_1:
               action_utils_standard[i] = -1 * cfr(i_map, next_history, card_1, card_2, pr_1 * strategy[i], pr_2, pr_c)
            else:
               action_utils_standard[i] = -1 * cfr(i_map, next_history,card_1, card_2, pr_1, pr_2 * strategy[i], pr_c)

    # Utility of information set.
        util = sum(action_utils_standard * strategy)
        regrets = action_utils_standard - util
        if is_player_1:
           info_set.regret_sum += pr_2 * pr_c * regrets
        else:
           info_set.regret_sum += pr_1 * pr_c * regrets

        return util
    
    #STANDARD CASE: ONLY RAISE AND CALL AVAILABLE
    else:
        for i, action in enumerate(["r", "c"]):
            next_history = history + action
            if is_player_1:
               action_utils_standard[i] = -1 * cfr(i_map, next_history, card_1, card_2, pr_1 * strategy[i], pr_2, pr_c)
            else:
               action_utils_standard[i] = -1 * cfr(i_map, next_history,card_1, card_2, pr_1, pr_2 * strategy[i], pr_c)

    # Utility of information set.
        util = sum(action_utils_standard * strategy)
        regrets = action_utils_standard - util
        if is_player_1:
           info_set.regret_sum += pr_2 * pr_c * regrets
        else:
           info_set.regret_sum += pr_1 * pr_c * regrets

        return util

def is_chance_node(history):

    return history == "" or history == "nncc" or history =="nnrc" or history == "nncrc" or history == "nncrrc" or history == "nnrrc"

def chance_util(i_map,history):
    if history == "":
       expected_value = 0
       n_possibilities = 9
       for i in range(_N_CARDS):
          for j in range(_N_CARDS):
              if i != j:
                expected_value += cfr(i_map, "nn", i, j, 
                                      1, 1, 1/n_possibilities)

       return expected_value/n_possibilities
   
    ##CASO SCELTA TRA 2 CARTE (AD INIZIO PARTITA I GIOCATORI HANNO RICEVUTO LA STESSA CARTA)
    elif():
       expected_value = 0
       n_possibilities = 2 
       for i in range(_N_CARDS):
          for j in range(_N_CARDS):
              if i != j:
                expected_value += cfr(i_map, history + "n", i, j, 
                                      1, 1, 1/n_possibilities)

       return expected_value/n_possibilities
   
    ##CASO SCELTA TRA 3 CARTE (AD INIZIO PARTITA I GIOCATORI HANNO RICEVUTO CARTE DIVERSE)
    else:
       expected_value = 0
       n_possibilities = 3
       for i in range(_N_CARDS):
          for j in range(_N_CARDS):
              if i != j:
                expected_value += cfr(i_map, history + "n", i, j, 
                                      1, 1, 1/n_possibilities)

       return expected_value/n_possibilities

def is_terminal(history):

    possibilities = {"nnrf": True, "nnrrf": True, "nnrrcnrf": True, "nnrrcnrc": True, "nnrrcnrrf": True,
                     "nnrrcnrrc": True, "nnrrcncc": True, "nnrrcncrf": True, "nnrrcncrc": True, "nnrrcncrrc": True,
                     "nnrrcncrrf": True,  #END OF FIRST SUBTREE
                     
                     "nnrcnrf": True, "nnrcnrc": True, "nnrcnrrf": True, "nnrcncrrf": True, "nnrcncrrc": True, 
                     "nnrcnrrc": True, "nnrcncc": True, "nnrcncrf": True, "nnrcncrc": True, #END OF SECOND SUBTREE
                     
                     
                     "nncrf": True, "nncrrf": True, "nncrrcnrf": True, "nncrrcnrc": True, "nncrrcnrrf": True,
                     "nncrrcnrrc": True, "nncrrcncc": True, "nncrrcncrf": True, "nncrrcncrc": True, "nncrrcncrrc": True,
                     "nncrrcncrrf": True,  #END OF THIRD SUBTREE
                     
                     "nncrcnrf": True, "nncrcnrc": True, "nncrcnrrf": True, "nncrcncrrf": True, "nncrcncrrc": True, 
                     "nncrcnrrc": True, "nncrcncc": True, "nncrcncrf": True, "nncrcncrc": True, #END OF FOURTH SUBTREE
                     
                     "nnccnrf": True, "nnccnrc": True, "nnccnrrf": True, "nnccncrrf": True, "nnccncrrc": True, 
                     "nnccnrrc": True, "nnccncc": True, "nnccncrf": True, "nnccncrc": True, #END OF FIFTH SUBTREE
                     
                     }

    return history in possibilities

#METHOD TO GET THE UTILITY OF TERMINAL NODES REACHED BEFORE THE THIRD ACTION OF NATURE (len(history) < 7)
def terminal_util_short(history, card_1, card_2):

    n = len(history)
    card_player = card_1 if n % 2 == 0 else card_2
    card_opponent = card_2 if n % 2 == 0 else card_1

    if history == "nncrf" or history == "nnrf": 
        # Last player folded. The current player wins.
        return 1
    
    elif history == "nncrrf" or history == "nnrrf":
        # Last player folded. The current player wins.
        return 3
    
    
 #METHOD TO GET THE UTILITY OF TERMINAL NODES 
def terminal_util_full(history, card_1, card_2, card_N):

    n = len(history)
    card_player = card_1 if n % 2 == 0 else card_2
    card_opponent = card_2 if n % 2 == 0 else card_1

   #LAST PLAYER FOLDED AFTER ONE RAISE (HAND AFTER SECOND NATURE)
    if history == "nnccncrf" or history == "nnccnrf":
        return 1
    
    #LAST PLAYER FOLDED AFTER TWO RAISE (HAND AFTER SECOND NATURE)
    if history == "nnccnrrf" or history == "nnccncrrf" or history == "nncrrcnrf" or history == "nncrrcncrf" or history == "nnrrcnrf" or history == "nnrrcncrf":
        return 5
    
     #LAST PLAYER FOLDED AFTER ONE RAISE CALLED BEFORE NATURE AND ONE RAISE AFTER NATURE
    if history == "nncrcnrf" or history == "nncrcncrf" or history == "nnrcnrf" or history == "nnrcncrf":
        return 3
    
     #LAST PLAYER FOLDED AFTER ONE RAISE CALLED BEFORE NATURE AND TWO RAISES AFTER NATURE
    if history == "nncrcnrrf" or history == "nncrcncrrf" or history == "nnrcncrrf" or history == "nnrcncrrf":
        return 7
    
    #LAST PLAYER FOLDS AFTER TWO RAISES BEFORE NATURE AND TWO RAISES AFTER NATURE
    if history == "nncrrcnrrf" or history == "nncrrcncrrf" or history == "nnrrcnrrf" or history == "nnrrcncrrf":
        return 9
    
    
    #ONLY CALLS
    if history == "nnccncc":
          if card_player > card_opponent or (card_player == card_N and card_opponent != card_N)  : 
              return 1
          elif(card_player == card_opponent): 
              return 0
          else:
              return -1
          
            
    #ONE RAISE BEFORE NATURE
    if history == "nnrcncc" or history == "nncrcncc":
          if card_player > card_opponent or (card_player == card_N and card_opponent != card_N)  : 
              return 3
          elif(card_player == card_opponent): 
              return 0
          else:
              return -3
          
    #ONE RAISE AFTER NATURE OR TWO RAISES BOTH BEFORE NATURE
    if history == "nnccnrc"  or history == "nnccncrc" or history == "nnrrcncc" or history == "nncrrcncc":
          if card_player > card_opponent or (card_player == card_N and card_opponent != card_N)  : 
              return 5
          elif(card_player == card_opponent): 
              return 0
          else:
              return -5
          
    #ONE RAISE AFTER NATURE AND ONE RAISE BEFORE NATURE
    if history == "nnrcnrc"   or history == "nnrcncrc"  or history == "nncrcnrc"  or history == "nncrcncrc" :
          if card_player > card_opponent or (card_player == card_N and card_opponent != card_N)  : 
              return 7
          elif(card_player == card_opponent): 
              return 0
          else:
              return -7
          
    
    
    #TWO RAISES AFTER NATURE OR TWO RAISES BEFORE NATURE AND ONE AFTER
    if history == "nnccnrrc" or history == "nnccncrrc" or history == "nnrrcnrc" or history =="nnrrcncrc" or history == "nncrrcnrc" or history == "nncrrcncrc" :
          if card_player > card_opponent or (card_player == card_N and card_opponent != card_N)  : 
              return 9
          elif(card_player == card_opponent): 
              return 0
          else:
              return -9
          
    #TWO RAISES AFTER NATURE AND ONE RAISE BEFORE NATURE
    if history == "nnrcnrrc"  or history == "nnrcncrrc" or history == "nncrcnrrc"  or history == "nncrcncrrc":
          if card_player > card_opponent or (card_player == card_N and card_opponent != card_N)  : 
              return 11
          elif(card_player == card_opponent): 
              return 0
          else:
              return -11
          
    #TWO RAISES AFTER NATURE AND TWO RAISES BEFORE NATURE
    if history == "nnrrcnrrc"  or history == "nnrrcncrrc"  or history == "nncrrcnrrc"  or history == "nncrrcncrrc" :
          if card_player > card_opponent or (card_player == card_N and card_opponent != card_N)  : 
              return 13
          elif(card_player == card_opponent): 
              return 0
          else:
              return -13
    
    
    
    
    

def card_str(card):
    if card == 0:
        return "J"
    elif card == 1:
        return "Q"
    return "K"


def get_info_set(i_map, card, history):

    key = card_str(card) + " " + history
    info_set = None

    if key not in i_map:
        info_set = InformationSet(key)
        i_map[key] = info_set
        return info_set

    return i_map[key]


#METHODS USED TO CALCULATE STRATEGIES GIVEN AN INFO SET AND DISPLAY RESULTS

class InformationSet():
    def __init__(self, key):
        self.key = key
        self.regret_sum = np.zeros(_N_ACTIONS)
        self.strategy_sum = np.zeros(_N_ACTIONS)
        self.strategy = np.repeat(1/_N_ACTIONS, _N_ACTIONS)
        self.reach_pr = 0
        self.reach_pr_sum = 0

    def next_strategy(self):
        self.strategy_sum += self.reach_pr * self.strategy
        self.strategy = self.calc_strategy()
        self.reach_pr_sum += self.reach_pr
        self.reach_pr = 0

    def calc_strategy(self):
        self.strategy_sum += self.reach_pr * self.strategy
        self.strategy = self.calc_strategy()
        self.reach_pr_sum += self.reach_pr
        self.reach_pr = 0

    def calc_strategy(self):
        strategy = self.make_positive(self.regret_sum)
        total = sum(strategy)
        if total > 0:
            strategy = strategy / total
        else:
            n = _N_ACTIONS
            strategy = np.repeat(1/n, n)

            return strategy

    def get_average_strategy(self):

        strategy = self.strategy_sum / self.reach_pr_sum

        # Purify to remove actions that are likely a mistake
        strategy = np.where(strategy < 0.001, 0, strategy)

        # Re-normalize
        total = sum(strategy)
        strategy /= total

        return strategy

    def make_positive(self, x):
        return np.where(x > 0, x, 0)

    def __str__(self):
        strategies = ['{:03.2f}'.format(x)
                      for x in self.get_average_strategy()]
        return '{} {}'.format(self.key.ljust(6), strategies)

def display_results(ev, i_map):
    print('player 1 expected value: {}'.format(ev))
    print('player 2 expected value: {}'.format(-1 * ev))

    print()
    print('player 1 strategies:')
    sorted_items = sorted(i_map.items(), key=lambda x: x[0])
    for _, v in filter(lambda x: len(x[0]) % 2 == 0, sorted_items):
        print(v)
    print()
    print('player 2 strategies:')
    for _, v in filter(lambda x: len(x[0]) % 2 == 1, sorted_items):
        print(v)

if __name__ == "__main__":
    main()

    
    
                    













                        
