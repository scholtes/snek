# =================================================================
# Rubik's Snake solver
# November 2019
# 
# See all closed solutions for the Rubik's Mini Snake below!
#  +-----------------------------------------------+
#  |  https://www.youtube.com/watch?v=EBAmBFG7DCg  |
#  |                    + + +                      |
#  |  https://www.youtube.com/watch?v=HPOI3N_4PEM  |
#  +-----------------------------------------------+
# 
# =================================================================
# TODO 
#   - replicate results from here???
#     http://blog.ylett.com/2011/09/rubiks-snake-combinations.html
#   - recursive backtrack to skip early failing solutions
#   - implement on GPU
# =================================================================

import argparse
import sys
import pyperclip
from collections import namedtuple
from itertools import chain, product
from math import asin, pi
from numpy import base_repr

#list(map(lambda c: int(c), '00103201110')) # => [0, 0, 1, 0, ..., 1, 0]
GLOBAL_CHECKS = 0

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

# ================== SOLVE STATES ====================
# Takes in a state and returns whether the state has no collisions
#   state:  string state, each element is '0' thru '3' ####<- YES, NO -> list of ints, each element is 0 thru 3
#   cyclic: if true then function returns true only if state is both
#           without collisions and forms a closed loop
def is_state_physical(state, n, cyclic = False):
    global GLOBAL_CHECKS
    GLOBAL_CHECKS += 1
    li_state = str_to_list_int(state)
    li_state.append(-1) # This is so that we still do the last collision check
    cells = {}
    curr_point = Point(0,0,0)
    curr_prism = Prism('+x','-y')
    fail_at = -1
    for rule in li_state:
        # ==== CYCLIC EARLY-FAIL ====
        if cyclic:
            remaining = n-fail_at
            if 2*abs(curr_point.x)>remaining or 2*abs(curr_point.y)>remaining+1 or 2*abs(curr_point.z)>remaining:
                return(False,fail_at)
        # ===== COLLISION CHECK =====
        if curr_point not in cells:
            # No prisms have entered the current cell
            cells[curr_point] = [curr_prism]
        elif len(cells[curr_point]) >= 2:
            # The current cell is already occupied by 2 prisms
            return (False,fail_at)
        elif __prisms_collide(curr_prism, cells[curr_point][0]):
            # The current cell is occupied by a prism that collides with the new one
            return (False,fail_at)
        else:
            # The current cell is occupied by a prism but there is room for the new one
            cells[curr_point].append(curr_prism)
        # ===========================
        # Break early if on augmented rule -1 (to do extra collision check)
        if rule == -1:
            break
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
        fail_at += 1
    if cyclic:
        # It is cyclic if the current point is (0,-1,0)
        # and the current leading face is +y.
        # This is because the initial prism is at (0,0,0)
        # and begins with an inner face of -y.
        return (curr_prism.lead == '+y' and curr_point == Point(0,-1,0), n-1)
    return (True,n-1)

# return whether two prisms (given to be in the same cell) collide
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

# applies all the rotation cycles to a prism given a rule
def __rotate(prism, rule):
    cycle_pos = CYCLES[prism.inner].index(prism.lead)
    new_lead = CYCLES[prism.inner][(cycle_pos+rule)%4]
    return Prism(new_lead, prism.inner)
# ====================================================



# ================ ENUMERATE STATES ==================
# Enumerates all possible solutions. Returns a generator of all states
#   physical: require no collisions?
#   cyclic: are cycles considered symmetric?
#   reverse: are reversals considered symmetric?
#   chiral: are chiral (left vs right, i.e., '1' vs '3') considered symmetric?
def enumerate_states(n, physical=False, reverse=False, chiral=False, cyclic=False):
    global GLOBAL_CHECKS
    GLOBAL_CHECKS = 0
    if not cyclic:
        yield from __enumerate_states(n,physical,reverse,chiral,cyclic)
    else:
        yield from __dedup_cyclic_states(__enumerate_states(n,physical,reverse,chiral,cyclic),reverse,chiral)



# Recursive backtracker to enumerate all possible states
#   prefix: a prefix to generate from
#   curr_len: used to track current length
# curr_len is redundant as this can be deduced from prefix, but this saves calls to len(prefix)
# EXAMPLES:
#   __enumerate(11, '', 0, False, False, False, False) will yield 4**11 times
#   __enumerate(11, '0123', 4, False, False, False, False) will yield 4**7 times
#       and will yield only states which match '0123*******'
# TODO backtracker doesn't step out early enough and checks too many states
#def __enumerate_states(n, prefix='', curr_len=0, physical=False, reverse=False, chiral=False, cyclic=False):
#    if curr_len == n:
#        state = normalize(prefix, reverse, chiral)
#        if state == prefix:
#            if physical:
#                if is_state_physical(state, cyclic):
#                    yield state
#                else:
#                    return
#            else:
#                yield state
#        else:
#            return
#    else:
#        yield from __enumerate_states(n, prefix+'0', curr_len+1, physical, reverse, chiral, cyclic)
#        yield from __enumerate_states(n, prefix+'1', curr_len+1, physical, reverse, chiral, cyclic)
#        yield from __enumerate_states(n, prefix+'2', curr_len+1, physical, reverse, chiral, cyclic)
#        yield from __enumerate_states(n, prefix+'3', curr_len+1, physical, reverse, chiral, cyclic)

def __enumerate_states(n, physical=False, reverse=False, chiral=False, cyclic=False):
    i = 0
    while i < 3*4**(n-1):
        state = base_repr(i, 4).rjust(n, "0")
        ### 3 check
        p3 = state.index("3") if "3" in state else n
        p1 = state.index("1") if "1" in state else n
        if p3 < p1:
            i = int((state[0:p3+1]).ljust(n,"0"),4) + 4**(n-1-p3)
            continue
        ### end 3 check
        normed = normalize(state, reverse, chiral)
        if state == normed:
            result = is_state_physical(state, n, cyclic)
            is_phyical = result[0]
            offset = result[1]
            if is_phyical:
                yield state
                i += 1
            else:
                i = int((state[0:offset+1]).ljust(n,"0"),4) + 4**(n-1-offset)
        else:
            i += 1;


# This normalization has to be done post-discovery instead of pre
# For reasons...
def __dedup_cyclic_states(states, reverse, chiral):
    used = set([])
    for state in states:
        if state not in used:
            yield state
        for aug_rule in range(4):
            aug_state = state + str(aug_rule)
            cycles = map(lambda i: (aug_state[i:]+aug_state[:i])[:-1], range(len(aug_state)))
            for cycle in cycles:
                used = used.union(set(__normalize_list(cycle, reverse, chiral)))




# Takes in a string state and returns the lexicographically minimum symmetric state
#   state: string state
#   reverse: are reversals considered symmetric?
#   chiral: are chiral (left vs right, i.e., '1' vs '3') considered symmetric?
# EXAMPLES
#   normalize('03000000',False,False) => # '03000000' -- always the identity
#   normalize('03000000',False,True) =>  # '03000000' -- switch 3 for 1
#   normalize('03000000',True,False) =>  # '00000030' -- reverse
#   normalize('03000000',True,True) =>   # '00000010' -- reverse and switch 3 for 1
def normalize(state, reverse=False, chiral=False):
    return min(__normalize_list(state,reverse,chiral))


def __normalize_list(state, reverse=False, chiral=False):
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
    '''
    # This ain't work
    if cyclic:
        states = chain.from_iterable(
            map(
                lambda st: map(lambda i: st[i:]+st[:i], range(len_state)),
                states))
    '''
    return states


def list_int_to_str(list_state):
    return ''.join(map(lambda c: str(c), list_state))

def str_to_list_int(state):
    return list(map(lambda c: int(c), state))
# ====================================================





def main():
    parser = argparse.ArgumentParser(description="Rubik's Mini Snake processor")
    parser.add_argument("--physical", type=str, help="Returns true if the given state is physically realizable")
    parser.add_argument("--draw", type=str, help="Prints OpenSCAD code to draw the given state")
    parser.add_argument("--solve", type=int, help="Counts the number of solutions for a Rubik's snake with SOLVE number prisms")
    parser.add_argument("--cyclic", action="store_true", help="Only return cyclic solutions and remove cyclic duplicates")
    parser.add_argument("--reverse", action="store_true", help="Remove duplicates under reverse symmetry")
    parser.add_argument("--chiral", action="store_true", help="Remove duplicates under chiral symmetry")
    parser.add_argument("--list", action="store_true", help="Makes --solve return all solutions instead of counting")
    parser.add_argument("--no-macro", action="store_true", help="Exclude the macro definitions from --draw. Useful for concatenating multiple states into 1 OpenSCAD file")
    parser.add_argument("--copy", action="store_true", help="Makes --draw copy output to clipboard")
    args = parser.parse_args()

    if args.physical:
        print(is_state_physical(args.physical, len(args.physical), args.cyclic))

    elif args.draw:
        openscad = draw_state(args.draw)
        if not args.no_macro:
            openscad = CODE_BASE + openscad
        print(openscad)
        if args.copy:
            pyperclip.copy(openscad)

    elif args.solve:
        states = enumerate_states(args.solve-1, physical=True, reverse=args.reverse, chiral=args.chiral, cyclic=args.cyclic)
        if args.list:
            for state in states:
                print(state)
        else:
            count = 0
            for state in states:
                count += 1
                if count %1000==0 or args.cyclic: print(f'\r{count}', end='')
                sys.stdout.flush()
            print(f'\r{count}')

    else:
        print("Must use one of --physical, --draw, or --solve. See --help for options")



if __name__ == '__main__':
    #main()
    for n in range(2,13): #2,13
        print(f"{2*n}: {len(list(enumerate_states(2*n-1, physical=True, reverse=True, chiral=True, cyclic=True)))} {GLOBAL_CHECKS}")