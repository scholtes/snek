# Garrett Scholtes
# November 2019
# 
# TODO replicate results below???
#   http://blog.ylett.com/2011/09/rubiks-snake-combinations.html
# ==============================================================

import argparse
from collections import namedtuple
from itertools import chain

#list(map(lambda c: int(c), '00103201110')) # => [0, 0, 1, 0, ..., 1, 0]

Point = namedtuple('Point', ['x', 'y', 'z'])
Prism = namedtuple('Prism', ['lead', 'inner'])


# Takes in a state and returns whether the state has no collisions
#   state:  string state, each element is '0' thru '3' ####<- YES, NO -> list of ints, each element is 0 thru 3
#   cyclic: if true then function returns true only if state is both
#           without collisions and forms a closed loop
def is_state_physical(state, cyclic = False):
    return True #TODO

# Takes in a string state and returns the lexicographically minimum symmetric state
#   state: string state
#   cyclic: are cycles considered symmetric?
#   reverse: are reversals considered symmetric?
#   chiral: are chiral (left vs right, i.e., 1 vs 3) considered symmetric?
def normalize(state, reverse=False, chiral=False, cyclic=False):
    len_state = len(state)
    states = [state]
    if reverse:
        states = chain.from_iterable(
            map(
                lambda st: (st, st[::-1]),
                states))
    if chiral:
        states = chain.from_iterable(
            map(
                lambda st: (st, ''.join(map(lambda c: {'0':'0','1':'3','2':'2','3':'1'}[c], st))),
                states))
    if cyclic:
        states = chain.from_iterable(
            map(
                lambda st: map(lambda i: st[i:]+st[:i], range(len_state)),
                states))
    return list(states)




def list_int_to_str(list_state):
    return ''.join(map(lambda c: str(c), list_state))

def str_to_list_int(state):
    return list(map(lambda c: int(c), state))