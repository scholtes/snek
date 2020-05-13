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
import time

#list(map(lambda c: int(c), '00103201110')) # => [0, 0, 1, 0, ..., 1, 0]
# # # # # GLOBAL_CHECKS = 0

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
    # # # # # global GLOBAL_CHECKS
    # # # # # GLOBAL_CHECKS += 1
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
    # # # # # global GLOBAL_CHECKS
    # # # # # GLOBAL_CHECKS = 0
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
    COUNTYDOO = -1
    YIELDS = 0
    while i < 3*4**(n-1):
        state = base_repr(i, 4).rjust(n, "0")
        #COUNTYDOO+=1
        #if COUNTYDOO % 10000 == 0:
        #    print(f"\rchecking {state}... (hit: {YIELDS})", end='')
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
                YIELDS += 1
                i += 1
            else:
                i = int((state[0:offset+1]).ljust(n,"0"),4) + 4**(n-1-offset)
        else:
            i += 1;


def __dedup_cyclic_states(states, reverse, chiral):
    used = set([])
    COUNTY = 0
    for state in states:
        unique = True
        for aug_rule in range(4):
            aug_state = state + str(aug_rule)
            cycles = map(lambda i: (aug_state[i:]+aug_state[:i])[:-1], range(len(aug_state)))
            for cycle in cycles:
                for normal in set(__normalize_list(cycle, reverse, chiral)):
                    if normal in used:
                        unique = False
                        break
                if not unique:
                    break
            if not unique:
                break
        if unique:
            COUNTY += 1
            print(f"{state} ({COUNTY})")
            used.add(state)
            yield state

# This normalization has to be done post-discovery instead of pre
# For reasons...
#def __dedup_cyclic_states(states, reverse, chiral):
#    used = set([])
#    COUNTY = 0
#    for state in states:
#        if state not in used:
#            COUNTY += 1
#            print(f"{state} ({COUNTY})")
#            yield state
#        for aug_rule in range(4):
#            aug_state = state + str(aug_rule)
#            cycles = map(lambda i: (aug_state[i:]+aug_state[:i])[:-1], range(len(aug_state)))
#            #TIME_1 = time.clock()
#            for cycle in cycles:
#                used = used.union(set(__normalize_list(cycle, reverse, chiral)))
#            #TIME_2 = time.clock()
#            #print(f"YIELD: {TIME_2 - TIME_1} {len(used)}")




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


#####################
####### DEBUG #######
def debug_thing():
    states_419 = ["0000123000012","0000131000031","0000131000113","0000131011102","0000132110002","0000210100303","0000210130102","0000213300113","0000213311102","0001131330002","0001132000331","0001132033302","0001200201101","0001200233013","0001200233331","0001200303303","0001200310332","0001200311031","0001200311113","0001201101102","0001201130031","0001201130113","0001201133332","0001201211032","0001210200101","0001210210302","0001213230002","0001230002321","0001230102303","0001230202101","0001230232302","0001233320031","0001233320113","0001233323332","0001310020131","0001310020213","0001311020031","0001311020113","0001312013302","0001312020331","0002130020031","0002131013302","0002131020331","0010022010012","0010023001101","0010023030112","0010023033013","0010023033331","0010023111031","0010023111113","0010031003001","0010031301031","0010113201031","0010113201113","0010113233303","0010113303001","0010113311003","0010120020212","0010120103200","0010120110023","0010120112021","0010120121202","0010120332001","0010121020112","0010121023013","0010121023331","0010121031101","0010121113001","0010121121003","0010123011123","0010123013321","0010123301201","0010123323203","0010123331021","0010123333023","0010130300200","0010130310203","0010130320202","0010130330201","0010131001013","0010131001331","0010131033101","0010131101021","0010131103023","0010131111201","0010131133203","0010131203031","0010131203113","0010131211303","0010210110101","0010210120302","0010212320102","0010212330303","0010213001021","0010213003023","0010213011201","0010213033203","0010213103031","0010213103113","0010213111303","0010213301013","0010213301331","0010213333101","0010220323302","0010220330013","0010220330331","0011013103012","0011021003302","0011021010331","0011021011112","0011021333012","0011022001102","0011022030113","0011320020231","0011320020313","0011320112002","0011323013302","0011323020013","0011323020331","0011323021112","0011323331002","0011331203012","0012002012032","0012002310231","0012002310313","0012003101123","0012003133231","0012003133313","0012003203101","0012003211013","0012003211331","0012003212112","0012011013023","0012011021201","0012011323231","0012011323313","0012011331123","0012012112123","0012012302102","0012012332303","0012013023001","0012013113303","0012013121031","0012013121113","0012021201101","0012021230112","0012021233013","0012021233331","0012021303303","0012021311031","0012021311113","0012102002032","0012102202012","0012300203210","0012301123023","0012301131201","0012301213101","0012320132001","0012320201210","0012320220212","0012320303200","0012320310023","0012320312021","0012320321202","0012321101201","0012321123203","0012321131021","0012321133023","0012321211123","0012321213321","0012323231101","0012323313001","0012330132023","0012330200210","0012331123001","0012331213303","0012333231123","0012333313023","0012333321201","0013001330210","0013002001300","0013002032333","0013002033110","0013002203102","0013023210331","0013032012123","0013033032023","0013033100210","0013101302201","0013102022011","0013102023110","0013102031300","0013102113200","0013102120023","0013102131202","0013103022033","0013110231123","0013110313023","0013111132023","0013111200210","0013120220231","0013120220313","0013200212331","0013202012011","0013202012333","0013202013110","0013202021300","0013202331210","0013203012133","0013203032311","0013211202200","0013230210101","0013230220302","0013233200200","0013233210203","0013233230201","0013302002011","0013302002333","0013302003110","0013302011300","0013302202113","0013302311202","0013302333200","0013303110200","0013303120203","0013303130202","0013311300200","0013311310203","0013311320202","0013311330201","0013312001331","0013312033101","0013312111201","0013312133203","0020020112330","0020020113111","0020020121301","0020021112333","0020021332113","0020112310202","0020112320201","0020113133202","0020113202331","0020120021031","0020121323202","0021011022023","0021013202201","0021020231333","0021020313233","0021020331211","0021022031331","0021030220103","0021102201113","0021112002333","0021202133013","0021232002123","0021310220313","0101101303012","0101123101032","0101131010113","0101131013332","0101131021102","0101131331032","0101132010231","0101132030131","0101132030213","0101132332012","0101133023302","0101133030331","0101133031112","0101133113012","0101201101132","0101201123312","0101203313302","0101203321112","0101210101303","0101210132332","0101210133031","0101210133113","0101210203321","0101210211131","0101210211213","0101210312112","0101211131112","0101213231032","0101213310113","0101213313332","0101230103123","0101230111313","0101230112132","0101233013032","0101233330313","0101233331132","0101310112012","0101310332032","0101311030313","0101311031132","0101311113032","0101312010131","0101312010213","0102101102032","0102101302012","0102130113032","0102133010213","0102133112012","0102133332032","0102201120113","0102201131102","0102203320231","0102203320313","0110120120232","0110123232303","0110131032321","0110131202302","0110131212101","0110210113321","0110210121131","0110212323331","0110213102302","0111022033302","0111123033332","0112012011201","0112012033203","0112012103113","0112012111303","0112012301331","0112012333101","0112310121232","0112310323212","0112320232023","0112320320232","0112321032303","0112330210203","0112330220202","0112330230201","0113032011303","0113032311201","0113032333203","0113033110203","0113033120202","0113033130201","0113101133212","0113101311232","0113102031330","0113102032111","0113102113230","0113102130232","0113111210203","0113111230201","0113120210113","0113133121232","0113133323212","0113201213102","0113202021330","0113202313202","0113203102203","0113230123203","0113230131021","0113230203231","0113230213321","0113233312021","0113233321202","0113302011330","0113302012111","0113302201302","0113302310232","0113303133232","0113303203102","0113303211332","0113311012021","0113311323232","0113312032321","0113321233332","0120121301230","0120130231112","0120130313012","0120131132012","0120212012112","0120213032012","0120323023202","0120323103230","0121012321123","0121012323321","0121013312133","0121013332311","0121112012111","0121112310232","0121112333230","0121113032333","0121113133232","0121121323232","0121323121232","0121323323212","0121331012133","0121331032311","0121331133212","0121331311232","0121332032111","0121332113230","0121332130232","0123020212320","0123022012302","0123232101303","0123323212021","0123331012333","0123332111230","0130231332321","0130232023203","0130232031021","0130232113321","0130232121213","0131133212021","0131202023130","0131202031320","0131211312021","0131212131021","0212021311131","0212331213321","1123211332123"]
    states_416 = ["0000123000012","0000131000031","0000131000113","0000131011102","0000132110002","0000210100303","0000210130102","0000213300113","0000213311102","0001131330002","0001132000331","0001132033302","0001200201101","0001200233013","0001200233331","0001200303303","0001200310332","0001200311031","0001200311113","0001201101102","0001201130031","0001201130113","0001201133332","0001201211032","0001210200101","0001210210302","0001213230002","0001230002321","0001230102303","0001230202101","0001230232302","0001233320031","0001233320113","0001233323332","0001310020131","0001310020213","0001311020031","0001311020113","0001312013302","0001312020331","0002130020031","0002131013302","0002131020331","0010022010012","0010023001101","0010023030112","0010023033013","0010023033331","0010023111031","0010023111113","0010031003001","0010031301031","0010113201031","0010113201113","0010113233303","0010113303001","0010113311003","0010120020212","0010120103200","0010120110023","0010120112021","0010120121202","0010120332001","0010121020112","0010121023013","0010121023331","0010121031101","0010121113001","0010121121003","0010123011123","0010123013321","0010123301201","0010123323203","0010123331021","0010123333023","0010130300200","0010130310203","0010130320202","0010130330201","0010131001013","0010131001331","0010131033101","0010131101021","0010131103023","0010131111201","0010131133203","0010131203031","0010131203113","0010131211303","0010210110101","0010210120302","0010212320102","0010212330303","0010213001021","0010213003023","0010213011201","0010213033203","0010213103031","0010213103113","0010213111303","0010213301013","0010213301331","0010213333101","0010220323302","0010220330013","0010220330331","0011013103012","0011021003302","0011021010331","0011021011112","0011021333012","0011022001102","0011022030113","0011320020231","0011320020313","0011320112002","0011323013302","0011323020013","0011323020331","0011323021112","0011323331002","0011331203012","0012002012032","0012002310231","0012002310313","0012003101123","0012003133231","0012003133313","0012003203101","0012003211013","0012003211331","0012003212112","0012011013023","0012011021201","0012011323231","0012011323313","0012011331123","0012012112123","0012012302102","0012012332303","0012013023001","0012013113303","0012013121031","0012013121113","0012021201101","0012021230112","0012021233013","0012021233331","0012021303303","0012021311031","0012021311113","0012102002032","0012102202012","0012300203210","0012301123023","0012301131201","0012301213101","0012320132001","0012320201210","0012320220212","0012320303200","0012320310023","0012320312021","0012320321202","0012321101201","0012321123203","0012321131021","0012321133023","0012321211123","0012321213321","0012323231101","0012323313001","0012330132023","0012330200210","0012331123001","0012331213303","0012333231123","0012333313023","0012333321201","0013001330210","0013002001300","0013002032333","0013002033110","0013002203102","0013023210331","0013032012123","0013033032023","0013033100210","0013101302201","0013102022011","0013102023110","0013102031300","0013102113200","0013102120023","0013102131202","0013103022033","0013110231123","0013110313023","0013111132023","0013111200210","0013120220231","0013120220313","0013200212331","0013202012011","0013202012333","0013202013110","0013202021300","0013202331210","0013203012133","0013203032311","0013211202200","0013230210101","0013230220302","0013233200200","0013233210203","0013233230201","0013302002011","0013302002333","0013302003110","0013302011300","0013302202113","0013302311202","0013302333200","0013303110200","0013303120203","0013303130202","0013311300200","0013311310203","0013311320202","0013311330201","0013312001331","0013312033101","0013312111201","0013312133203","0020020112330","0020020113111","0020020121301","0020021112333","0020021332113","0020112310202","0020112320201","0020113133202","0020113202331","0020120021031","0020121323202","0021011022023","0021013202201","0021020231333","0021020313233","0021020331211","0021022031331","0021030220103","0021102201113","0021112002333","0021202133013","0021232002123","0021310220313","0101101303012","0101123101032","0101131010113","0101131013332","0101131021102","0101131331032","0101132010231","0101132030131","0101132030213","0101132332012","0101133023302","0101133030331","0101133031112","0101133113012","0101201101132","0101201123312","0101203313302","0101203321112","0101210101303","0101210132332","0101210133031","0101210133113","0101210203321","0101210211131","0101210211213","0101210312112","0101211131112","0101213231032","0101213310113","0101213313332","0101230103123","0101230111313","0101230112132","0101233013032","0101233330313","0101233331132","0101310112012","0101310332032","0101311031132","0101311113032","0101312010213","0102101102032","0102101302012","0102130113032","0102133112012","0102133332032","0102201120113","0102201131102","0102203320231","0102203320313","0110120120232","0110123232303","0110131032321","0110131202302","0110131212101","0110210113321","0110210121131","0110212323331","0110213102302","0111022033302","0111123033332","0112012011201","0112012033203","0112012103113","0112012111303","0112012301331","0112012333101","0112310121232","0112310323212","0112320232023","0112320320232","0112321032303","0112330210203","0112330220202","0112330230201","0113032011303","0113032311201","0113032333203","0113033110203","0113033120202","0113033130201","0113101133212","0113101311232","0113102031330","0113102032111","0113102113230","0113102130232","0113111210203","0113111230201","0113120210113","0113133121232","0113133323212","0113201213102","0113202021330","0113202313202","0113203102203","0113230123203","0113230131021","0113230203231","0113230213321","0113233312021","0113233321202","0113302011330","0113302012111","0113302201302","0113302310232","0113303133232","0113303203102","0113303211332","0113311012021","0113311323232","0113312032321","0113321233332","0120121301230","0120130231112","0120130313012","0120131132012","0120212012112","0120213032012","0120323023202","0120323103230","0121012321123","0121012323321","0121013312133","0121013332311","0121112012111","0121112310232","0121112333230","0121113032333","0121113133232","0121121323232","0121323121232","0121323323212","0121331012133","0121331032311","0121331133212","0121331311232","0121332032111","0121332113230","0121332130232","0123020212320","0123022012302","0123232101303","0123323212021","0123331012333","0123332111230","0130231332321","0130232023203","0130232031021","0130232113321","0130232121213","0131133212021","0131202023130","0131202031320","0131211312021","0131212131021","0212021311131","0212331213321","1123211332123"]

    all_states = []
    for state in states_416:
        state_set = set([])
        for aug_rule in range(4):
            aug_state = state + str(aug_rule)
            cycles = map(lambda i: (aug_state[i:]+aug_state[:i])[:-1], range(len(aug_state)))
            for cycle in cycles:
                state_set = state_set.union(set(__normalize_list(cycle, True, True)))
        all_states.extend(list(state_set))

    print(f"Too high: {419*4*14*2*2}")
    print(f"Expected (calc): {len(all_states)}")
    print(f"Actual: {len(set(all_states))}")
####### DEBUG #######
#####################


if __name__ == '__main__':
    #main()
    #for n in range(2,13): #2,13
    #    print(f"\r            {' '*(2*n-1)}\r{2*n}: {len(list(enumerate_states(2*n-1, physical=True, reverse=True, chiral=True, cyclic=True)))}")
    debug_thing()