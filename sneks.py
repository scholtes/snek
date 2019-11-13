# Garrett Scholtes
# November 2019
# 
# TODO replicate results below???
#   http://blog.ylett.com/2011/09/rubiks-snake-combinations.html
# ==============================================================

import argparse
from collections import namedtuple
from itertools import chain, product

#list(map(lambda c: int(c), '00103201110')) # => [0, 0, 1, 0, ..., 1, 0]

# ================ PREDEFINED OBJECTS ================
Point = namedtuple('Point', ['x', 'y', 'z'])
Prism = namedtuple('Prism', ['lead', 'inner'])
FLIP = {
    '+x': '-x',
    '+y': '-y',
    '+z': '-z',
    '-x': '+x',
    '-y': '+y',
    '-z': '+z',
}
FNTP = {
    '+x': Point(1,0,0),
    '+y': Point(0,1,0),
    '+z': Point(0,0,1),
    '-x': Point(-1,0,0),
    '-y': Point(0,-1,0),
    '-z': Point(0,0,-1),
}
CYCLES = {
    '+x': ('+y','+z','-y','-z'),
    '+y': ('+z','+x','-z','-x'),
    '+z': ('+x','+y','-x','-y'),
    '-x': ('+z','+y','-z','-y'),
    '-y': ('+x','+z','-x','-z'),
    '-z': ('+y','+x','-y','-x'),
}
# ====================================================


# Takes in a state and returns whether the state has no collisions
#   state:  string state, each element is '0' thru '3' ####<- YES, NO -> list of ints, each element is 0 thru 3
#   cyclic: if true then function returns true only if state is both
#           without collisions and forms a closed loop
def is_state_physical(state, cyclic = False):
    li_state = str_to_list_int(state)
    cells = {}
    curr_point = Point(0,0,0)
    curr_prism = Prism('+x','-y')
    for rule in li_state:
        # ===== COLLISION CHECK =====
        if curr_point not in cells:
            # No prisms have entered the current cell
            cells[curr_point] = [curr_prism]
        elif len(cells[curr_point]) >= 2:
            # The current cell is already occupied by 2 prisms
            return False
        elif __prisms_collide(curr_prism, cells[curr_point][0]):
            # The current cell is occupied by a prism that collides with the new one
            return False
        else:
            # The current cell is occupied by a prism but there is room for the new one
            cells[curr_point].append(curr_prism)
        # ===========================
        # Compute successor permutation
        diff_point = __face_name_to_point(curr_prism.lead)
        succ_point = Point(
            curr_point.x + diff_point.x,
            curr_point.y + diff_point.y,
            curr_point.z + diff_point.z
        )
        # Compute successor orientation
        succ_prism = Prism(FLIP[curr_prism.inner], FLIP[curr_prism.lead])
        succ_prism = __rotate(succ_prism, rule)
        # Increment current
        curr_point = succ_point
        curr_prism = succ_prism
    return True #TODO

def __prisms_collide(prism1, prism2):
    return (not(
        (prism1.lead == FLIP[prism2.lead] and prism1.inner == FLIP[prism2.inner])
            or
        (prism1.lead == FLIP[prism2.inner] and prism1.inner == FLIP[prism2.lead])
    ))

# E.g., '-y' => Point(0, -1, 0)
def __face_name_to_point(face):
    pt = FNTP[face]
    return Point(pt.x, pt.y, pt.z)

def __rotate(prism, rule):
    cycle_pos = CYCLES[prism.inner].index(prism.lead)
    new_lead = CYCLES[prism.inner][(cycle_pos+rule)%4]
    return Prism(new_lead, prism.inner)


# Enumerates all possible solutions. Returns a generator of all states
#   physical: require no collisions?
#   cyclic: are cycles considered symmetric?
#   reverse: are reversals considered symmetric?
#   chiral: are chiral (left vs right, i.e., '1' vs '3') considered symmetric?
def enumerate_states(n, physical=False, reverse=False, chiral=False, cyclic=False):
    yield from __enumerate_states(n,'',0,physical,reverse,chiral,cyclic)

# Recursive backtracker to enumerate all possible states
#   prefix: a prefix to generate from
#   curr_len: used to track current length
# curr_len is redundant as this can be deduced from prefix, but this saves calls to len(prefix)
# EXAMPLES:
#   __enumerate(11, '', 0, False, False, False, False) will yield 4**11 times
#   __enumerate(11, '0123', 4, False, False, False, False) will yield 4**7 times
#       and will yield only states which match '0123*******'
# TODO backtracker doesn't step out early enough and checks too many states
def __enumerate_states(n, prefix='', curr_len=0, physical=False, reverse=False, chiral=False, cyclic=False):
    if curr_len == n:
        state = normalize(prefix, reverse, chiral, cyclic)
        if state == prefix:
            if physical:
                if is_state_physical(state, cyclic):
                    yield state
                else:
                    return
            else:
                yield state
        else:
            return
    else:
        yield from __enumerate_states(n, prefix+'0', curr_len+1, physical, reverse, chiral, cyclic)
        yield from __enumerate_states(n, prefix+'1', curr_len+1, physical, reverse, chiral, cyclic)
        yield from __enumerate_states(n, prefix+'2', curr_len+1, physical, reverse, chiral, cyclic)
        yield from __enumerate_states(n, prefix+'3', curr_len+1, physical, reverse, chiral, cyclic)




# Takes in a string state and returns the lexicographically minimum symmetric state
#   state: string state
#   cyclic: are cycles considered symmetric?
#   reverse: are reversals considered symmetric?
#   chiral: are chiral (left vs right, i.e., '1' vs '3') considered symmetric?
# EXAMPLES
#   normalize('010322',True,True,True) => # '010223' -- reverse then cycle left by 3
#   normalize('03000000',True,True,True) => # '00000001' -- chiral then cycle left by 2
#   normalize('03000000',False,False,False) => # '03000000' -- always the identity
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
    return min(states)


def list_int_to_str(list_state):
    return ''.join(map(lambda c: str(c), list_state))

def str_to_list_int(state):
    return list(map(lambda c: int(c), state))



# TODO actually use correctly
if __name__ == '__main__':
    states = list(enumerate_states(4, physical=True, reverse=True, chiral=True, cyclic=False))
    print(len(states))
    for state in states: print(state)
