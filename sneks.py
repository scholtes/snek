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
from math import asin, pi

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
with open("_snekbase.scad", 'r+') as f: CODE_BASE = f.read()
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
        yield from __dedup_cyclic_states(__enumerate_states(n,'',0,physical,reverse,chiral,cyclic),reverse,chiral)



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
#   cyclic: are cycles considered symmetric?
#   reverse: are reversals considered symmetric?
#   chiral: are chiral (left vs right, i.e., '1' vs '3') considered symmetric?
# EXAMPLES
#   normalize('03000000',False,False) => # '03000000' -- always the identity
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










def draw_all_solutions_in_grid(sols):
    count = 0
    code = CODE_BASE
    for x in range(-4, 5):
        for y in range(-4, 5):
            code += draw_state(sols[count], Point(4*x,4*y,0))
            count += 1
            if count >= len(sols):
                break
        if count >= len(sols):
                break
    print(code)
    pyperclip.copy(code)
    return code

def draw_all_solutions_in_line(sols):
    count = 0
    code = CODE_BASE
    code += "\n"
    code += "\ntranslate([(-82*$t+9)*4, 0, 0]){"
    code += "\nrotate([-$t*360*70/5,0,0]){\n"
    for x in range(70):
        if x == 0:
            code += "if($t < 0.3333) {"
        if x == 24:
            code += "}if(0.3333 < $t && $t < 0.666) { "
        if x == 48:
            code += "}if(0.6666 < $t) { "
        code += draw_state(sols[x], Point(4*x,0,0))
    code += "\n}\n}\n}\n"
    print(code)
    pyperclip.copy(code)
    return code

def draw_all_solutions_at_center(sols):
    def _f_(x):
        return (asin(2*x-1)+pi/2)/pi
    def _fff_(x):
        return _f_(_f_(x))
    count = 0
    code = CODE_BASE
    code += "\nfunction fancy_rot(t) = (1-cos(t*180))/2;"
    for x in range(70):
        if x == 0:
            code += f"if($t < {_fff_((x+1)/70)}) {{"
        elif x != 69:
            code += f"}}if({_fff_((x)/70)} < $t && $t <= {_fff_((x+1)/70)}) {{"
        else:
            code += f"}}if({_fff_((x)/70)} < $t) {{"
        code += "\nrotate([0,0,-360*2*fancy_rot(fancy_rot(fancy_rot($t)))]){\n"
        code += draw_state(sols[x])
        code += "\n}"
        code += f'\ncolor("#99ff33"){{translate([0,-3,3]){{scale(0.05){{rotate([90,0,90]){{text("{sols[x]}");}}}}}}}}\n'
        code += f'\ncolor("#99ff33"){{translate([0,-3,4]){{scale(0.05){{rotate([90,0,90]){{text("Solution {x+1}");}}}}}}}}\n'
    code += "\n}\n"
    print(code)
    pyperclip.copy(code)
    return code


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
        print(is_state_physical(args.physical, args.cyclic))

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

# TODO actually use correctly
if __name__ == '__main__':
    main()
    #count = 0
    #for state in enumerate_states(11, physical=True, reverse=True, chiral=True, cyclic=True):
    #    count += 1
    #    sys.stdout.write(f'{count}: {state}\n')
    #    #if count %1000==0: print(f'\r{count}',end='')
    #    sys.stdout.flush()
    #print(f"\r{count}")

    #print(len(states))
    #for state in states: print(state)
    #print(is_state_physical('2222'))

    #code = CODE_BASE 
    #code += draw_state("00013130000")
    #pyperclip.copy(code)
    #print(code)

    # All 41 cyclic solutions for Rubik's mini
    #sols = ["00002200002","00012300032","00101200303","00101230102","00120031002","00120113302","00120120013",
    #"00120120331","00120121112","00123002123","00123202303","00123212102","00123302101","00130013001","00130323013",
    #"00130323331","00130331101","00132023203","00132031021","00132033023","00132111123","00132113321","00200200200",
    #"00200210203","00200220202","00201210101","01101201101","01101233013","01101233331","01101303303","01101311031",
    #"01101311113","01123033113","01123101123","01123103321","01123203101","01123211013","01123211331","01131013023",
    #"01131021201","01131331123","01131333321","01132302102","01132332303","01133113303","01133121031","01133121113",
    #"01201213321","01210123202","01210132023","01210203230","01213231123","01213233321","01213313023","01230201230",
    #"01233231303","01233313203","01233321021","01303101303","01303133113","01311323113","02123202321","11113133331",
    #"11121323331","11213233231","11213311331","11313311313","11313312132","11331133113","12132312132"]
    #draw_all_solutions_at_center(sols)
