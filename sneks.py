# Garrett Scholtes
# November 2019
# 
# TODO replicate results below???
#   http://blog.ylett.com/2011/09/rubiks-snake-combinations.html
# ==============================================================

import argparse
import sys
import pyperclip
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

# ================== SOLVE STATES ====================
# Takes in a state and returns whether the state has no collisions
#   state:  string state, each element is '0' thru '3' ####<- YES, NO -> list of ints, each element is 0 thru 3
#   cyclic: if true then function returns true only if state is both
#           without collisions and forms a closed loop
def is_state_physical(state, cyclic = False):
    li_state = str_to_list_int(state)
    li_state.append(-1) # This is so that we still do the last collision check
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
    if cyclic:
        # It is cyclic if the current point is (0,-1,0)
        # and the current leading face is +y.
        # This is because the initial prism is at (0,0,0)
        # and begins with an inner face of -y.
        return curr_prism.lead == '+y' and curr_point == Point(0,-1,0)
    return True

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
# ====================================================

# ================== DRAW STATES =====================
CODE_BASE = ""
with open("snekbase.scad", 'r+') as f: CODE_BASE = f.read()
ROTATES = {
    Prism("-x","-y"): (-0*90,-2*90,0),
    Prism("-z","-y"): (-0*90,-3*90,0),
    Prism("+x","-y"): (-0*90,-0*90,0),
    Prism("+z","-y"): (-0*90,-1*90,0),
    Prism("-z","-x"): (-1*90,-2*90,0),
    Prism("+x","-z"): (-1*90,-3*90,0),
    Prism("+z","+x"): (-1*90,-0*90,0),
    Prism("-x","+z"): (-1*90,-1*90,0),
    Prism("-x","+y"): (-2*90,-2*90,0),
    Prism("-z","+y"): (-2*90,-3*90,0),
    Prism("+x","+y"): (-2*90,-0*90,0),
    Prism("+z","+y"): (-2*90,-1*90,0)
}

# Returns OpenSCAD code
def draw_state(state,offset=Point(0,0,0),center=True):
    li_state = str_to_list_int(state)
    li_state.append(-1) # This is so that we still do the last collision check
    curr_point = Point(0,0,0)
    curr_prism = Prism('+x','-y')
    code = ""
    INDENT = ""
    if center:
        INDENT = " "*4
    color0 = "blue"
    color1 = "white"
    r1,r2,r3 = 0,0,0 #TODO actually compute this somehow
    s = 1
    # For doing center logic
    center_of_mass = Point(0,0,0)
    for rule in li_state:
        # ========== DRAW ===========
        x,y,z = curr_point.x+offset.x, curr_point.y+offset.y, curr_point.z+offset.z
        code += f'{INDENT}block({x},{y},{z},{r1},{r2},{r3},"{color0}","{color1}");\n'
        # ===========================
        # Break early if on augmented rule -1 (to do extra draw )
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
        # == Prepare for next draw ==
        color0,color1 = color1,color0
        r1,r2,r3 = __rotations_from_prism(curr_prism)
        # ===========================
        center_of_mass = Point(
            center_of_mass.x + curr_point.x,
            center_of_mass.y + curr_point.y,
            center_of_mass.z + curr_point.z
        )
    if center:
        count = len(state)
        center_of_mass = Point(
            center_of_mass.x/count,
            center_of_mass.y/count,
            center_of_mass.z/count
        )
        code = f"translate([{-center_of_mass.x},{-center_of_mass.y},{-center_of_mass.z}]) {{\n{code}}}"
    return code

# Says what angles to rotate a prism by from the initial
def __rotations_from_prism(curr_prism):
    if curr_prism in ROTATES:
        return ROTATES[curr_prism]
    else:
        flipped_faces = Prism(curr_prism.inner, curr_prism.lead)
        return ROTATES[flipped_faces]
# ====================================================


# ================ ENUMERATE STATES ==================
# Enumerates all possible solutions. Returns a generator of all states
#   physical: require no collisions?
#   cyclic: are cycles considered symmetric?
#   reverse: are reversals considered symmetric?
#   chiral: are chiral (left vs right, i.e., '1' vs '3') considered symmetric?
def enumerate_states(n, physical=False, reverse=False, chiral=False, cyclic=False):
    if not cyclic:
        yield from __enumerate_states(n,'',0,physical,reverse,chiral,cyclic)
    else:
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
        state = normalize(prefix, reverse, chiral)
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
#   normalize('03000000',False,False) => # '03000000' -- always the identity
def normalize(state, reverse=False, chiral=False):
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
    return min(states)


def list_int_to_str(list_state):
    return ''.join(map(lambda c: str(c), list_state))

def str_to_list_int(state):
    return list(map(lambda c: int(c), state))
# ====================================================










def draw_all_solutions_in_grid(sols):
    count = 0
    code = CODE_BASE
    for x in range(-3, 4):
        for y in range(-3, 4):
            code += draw_state(sols[count], Point(4*x,4*y,0))
            count += 1
            if count >= len(sols):
                break
        if count >= len(sols):
                break
    print(code)
    pyperclip.copy(code)
    return code

# TODO actually use correctly
if __name__ == '__main__':
    count = 0
    for state in enumerate_states(11, physical=True, reverse=True, chiral=True, cyclic=True):
        count += 1
        sys.stdout.write(f'{count}: {state}\n')
        sys.stdout.flush()

    #print(len(states))
    #for state in states: print(state)
    #print(is_state_physical('2222'))

    #print(draw_state("01321132312"))

    # All 41 cyclic solutions for Rubik's mini
    #sols = ["00101230102","00120031002","00120113302","00120120013","00120120331","00120121112","00123212102",
    #"00123332302","00130320112","00130323331","00131102302","00210120212","01012301022","01101233013","01101233331",
    #"01101310332","01101311113","01102130113","01102133332","01123033113","01123211013","01123211331","01131013023",
    #"01131331123","01131333321","01132302102","01133121031","01133121113","01201203231","01201211123","01201213321",
    #"01210123202","01210220232","01213231123","01213233321","01311121331","01311323113","01321111231","01321112132",
    #"01321132312","01321133213"]
    #draw_all_solutions_in_grid(sols)
