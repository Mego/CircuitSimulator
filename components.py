#!/usr/bin/env python3

import copy

class NamedTuple:

    __slots__ = ('container',)
    
    def __init__(self, **kwargs):
        self.container = kwargs
        
    def __getattr__(self, attr):
        return self.container[attr]

class Board:

    __slots__ = ('board',)

    def __init__(self):
        self.board = {}
        
    def doTick(self):
        nextboard = copy.deepcopy(self.board)
        for loc, comp in self.board.items():
            comp.compute()
            nextboard[loc].clear()
            x,y = loc
            if comp.top:
                nextboard[(x,y-1)].bottom = True
            if comp.left:
                nextboard[(x-1,y)].right = True
            if comp.bottom:
                nextboard[(x,y+1)].top = True
            if comp.right:
                nextboard[(x+1,y)].left = True

class Component:

    __slots__ = ('top', 'left', 'bottom', 'right', 'loc', 'pass_rule', 'size')

    def __init__(self, x, y, pass_rule = None, size = (1,1)):
        self.top = False
        self.left = False
        self.bottom = False
        self.right = False
        self.loc = (x,y)
        self.size = size
        self.pass_rule = pass_rule or (lambda top,left,bottom,right:(False,False,False,False))
        
    def clear(self):
        self.top = self.left = self.right = self.bottom = False
        
    def compute(self):
        self.top, self.left, self.bottom, self.right = self.pass_rule(self.top, self.left, self.bottom, self.right)
        
class DelayComponent(Component):
    
    __slots__ = ('stored_bit', 'ticks_since_store', 'store_rule', 'output_rule')
    
    def __init__(self, x, y, store_rule=None, output_rule=None, delay = 1, size = (1,1)):
        super().__init__(x, y, None, size)
        self.stored_bit = False
        self.ticks_since_store = 0
        self.store_rule = store_rule or lambda t,l,b,r:False
        self.output_rule = output_rule or lambda s,t:(False,False,False,False)
        
    def clear(self):
        super().clear()
        self.stored_bit = False
        self.ticks_since_store = 0
        
    def compute(self):
        t,l,b,r = output_rule(self.stored_bit, self.ticks_since_store)
        s = store_rule(self.top, self.left, self.bottom, self.right)
        if s:
            self.ticks_since_store = 0
        self.ticks_since_store += 1
        self.top, self.left, self.bottom, self.right = t,l,b,r
        self.stored_bit = s
        
def simple_component_maker(pass_rule = None):
    return (lambda x,y: Component(x, y, pass_rule))
    
# Wire (reversible) components
WIRES = NamedTuple(
    # Opposing outputs
    L_R_WIRE = simple_component_maker(lambda t,l,b,r:(False,r,False,l)),
    T_B_WIRE = simple_component_maker(lambda t,l,b,r:(b,False,t,False)),
    # Adjacent outputs
    T_R_WIRE = simple_component_maker(lambda t,l,b,r:(r,False,False,t)),
    L_B_WIRE = simple_component_maker(lambda t,l,b,r:(False,b,l,False)),
    L_T_WIRE = simple_component_maker(lambda t,l,b,r:(l,t,False,False)),
    B_R_WIRE = simple_component_maker(lambda t,l,b,r:(False,False,r,b)),
)

# Gate (non-reversible) components
AND_GATES = NamedTuple(
    # Opposing inputs, single output
    TB_R_AND = simple_component_maker(lambda t,l,b,r:(False,False,False,t and b)),
    LR_B_AND = simple_component_maker(lambda t,l,b,r:(False,False,l and r,False)),
    TB_L_AND = simple_component_maker(lambda t,l,b,r:(False,t and b,False,False)),
    LR_T_AND = simple_component_maker(lambda t,l,b,r:(l and r,False,False,False)),
    # Adjacent inputs, single output
    TL_B_AND = simple_component_maker(lambda t,l,b,r:(False,False,False,t and l)),
    TL_R_AND = simple_component_maker(lambda t,l,b,r:(False,False,t and l,False)),
    LB_T_AND = simple_component_maker(lambda t,l,b,r:(l and b,False,False,False)),
    LB_R_AND = simple_component_maker(lambda t,l,b,r:(False,False,False,l and b)),
    BR_T_AND = simple_component_maker(lambda t,l,b,r:(b and r,False,False,False)),
    BR_L_AND = simple_component_maker(lambda t,l,b,r:(False,b and r,False,False)),
    RT_L_AND = simple_component_maker(lambda t,l,b,r:(False,r and t,False,False)),
    RT_B_AND = simple_component_maker(lambda t,l,b,r:(False,False,r and t,False)),
    # Adjacent inputs, two outputs
    TL_BR_AND = simple_component_maker(lambda t,l,b,r:(False,False,t and l,t and l)),
    LB_TR_AND = simple_component_maker(lambda t,l,b,r:(l and b,False,False,l and b)),
    BR_TL_AND = simple_component_maker(lambda t,l,b,r:(b and r,b and r,False,False)),
    RT_BL_AND = simple_component_maker(lambda t,l,b,r:(False,r and t,r and t,False)),
)

XOR_GATES = NamedTuple(
    # Opposing inputs, single output
    TB_R_XOR = simple_component_maker(lambda t,l,b,r:(False,False,False,t ^ b)),
    LR_B_XOR = simple_component_maker(lambda t,l,b,r:(False,False,l ^ r,False)),
    TB_L_XOR = simple_component_maker(lambda t,l,b,r:(False,t ^ b,False,False)),
    LR_T_XOR = simple_component_maker(lambda t,l,b,r:(l ^ r,False,False,False)),
    # Adjacent inputs, single output
    TL_B_XOR = simple_component_maker(lambda t,l,b,r:(False,False,False,t ^ l)),
    TL_R_XOR = simple_component_maker(lambda t,l,b,r:(False,False,t ^ l,False)),
    LB_T_XOR = simple_component_maker(lambda t,l,b,r:(l ^ b,False,False,False)),
    LB_R_XOR = simple_component_maker(lambda t,l,b,r:(False,False,False,l ^ b)),
    BR_T_XOR = simple_component_maker(lambda t,l,b,r:(b ^ r,False,False,False)),
    BR_L_XOR = simple_component_maker(lambda t,l,b,r:(False,b ^ r,False,False)),
    RT_L_XOR = simple_component_maker(lambda t,l,b,r:(False,r ^ t,False,False)),
    RT_B_XOR = simple_component_maker(lambda t,l,b,r:(False,False,r ^ t,False)),
    # Adjacent inputs, two outputs
    TL_BR_XOR = simple_component_maker(lambda t,l,b,r:(False,False,t ^ l,t ^ l)),
    LB_TR_XOR = simple_component_maker(lambda t,l,b,r:(l ^ b,False,False,l ^ b)),
    BR_TL_XOR = simple_component_maker(lambda t,l,b,r:(b ^ r,b ^ r,False,False)),
    RT_BL_XOR = simple_component_maker(lambda t,l,b,r:(False,r ^ t,r ^ t,False)),
)

OR_GATES = NamedTuple(
    # Opposing inputs, single output
    TB_R_OR = simple_component_maker(lambda t,l,b,r:(False,False,False,t or b)),
    LR_B_OR = simple_component_maker(lambda t,l,b,r:(False,False,l or r,False)),
    TB_L_OR = simple_component_maker(lambda t,l,b,r:(False,t or b,False,False)),
    LR_T_OR = simple_component_maker(lambda t,l,b,r:(l or r,False,False,False)),
    # Adjacent inputs, single output
    TL_B_OR = simple_component_maker(lambda t,l,b,r:(False,False,False,t or l)),
    TL_R_OR = simple_component_maker(lambda t,l,b,r:(False,False,t or l,False)),
    LB_T_OR = simple_component_maker(lambda t,l,b,r:(l or b,False,False,False)),
    LB_R_OR = simple_component_maker(lambda t,l,b,r:(False,False,False,l or b)),
    BR_T_OR = simple_component_maker(lambda t,l,b,r:(b or r,False,False,False)),
    BR_L_OR = simple_component_maker(lambda t,l,b,r:(False,b or r,False,False)),
    RT_L_OR = simple_component_maker(lambda t,l,b,r:(False,r or t,False,False)),
    RT_B_OR = simple_component_maker(lambda t,l,b,r:(False,False,r or t,False)),
    # Adjacent inputs, two outputs
    TL_BR_OR = simple_component_maker(lambda t,l,b,r:(False,False,t or l,t or l)),
    LB_TR_OR = simple_component_maker(lambda t,l,b,r:(l or b,False,False,l or b)),
    BR_TL_OR = simple_component_maker(lambda t,l,b,r:(b or r,b or r,False,False)),
    RT_BL_OR = simple_component_maker(lambda t,l,b,r:(False,r or t,r or t,False)),
)

AND_NOT_GATES = NamedTuple(
    # Opposing inputs, single output
    TB_R_ANT = simple_component_maker(lambda t,l,b,r:(False,False,False,t and not b)),
    TB_L_ANT = simple_component_maker(lambda t,l,b,r:(False,t and not b,False,False)),
    LR_T_ANT = simple_component_maker(lambda t,l,b,r:(l and not r,False,False,False)),
    LR_B_ANT = simple_component_maker(lambda t,l,b,r:(False,False,l and not r,False)),
    BT_R_ANT = simple_component_maker(lambda t,l,b,r:(False,False,False,b and not t)),
    BT_L_ANT = simple_component_maker(lambda t,l,b,r:(False,b and not t,False,False)),
    RL_T_ANT = simple_component_maker(lambda t,l,b,r:(r and not l,False,False,False)),
    RL_B_ANT = simple_component_maker(lambda t,l,b,r:(False,False,r and not l,False)),
    # Adjacent inputs, single output
    TL_B_ANT = simple_component_maker(lambda t,l,b,r:(False,False,t and not l,False)),
    TL_R_ANT = simple_component_maker(lambda t,l,b,r:(False,False,False,t and not l)),
    LB_T_ANT = simple_component_maker(lambda t,l,b,r:(l and not b,False,False,False)),
    LB_R_ANT = simple_component_maker(lambda t,l,b,r:(False,False,False,l and not b)),
    BR_T_ANT = simple_component_maker(lambda t,l,b,r:(b and not r,False,False,False)),
    BR_L_ANT = simple_component_maker(lambda t,l,b,r:(False,b and not r,False,False)),
    RT_L_ANT = simple_component_maker(lambda t,l,b,r:(False,r and not t,False,False)),
    RT_B_ANT = simple_component_maker(lambda t,l,b,r:(False,False,r and not t,False)),
    LT_B_ANT = simple_component_maker(lambda t,l,b,r:(False,False,l and not t,False)),
    LT_R_ANT = simple_component_maker(lambda t,l,b,r:(False,False,False,l and not t)),
    BL_T_ANT = simple_component_maker(lambda t,l,b,r:(b and not l,False,False,False)),
    BL_R_ANT = simple_component_maker(lambda t,l,b,r:(False,False,False,b and not l)),
    RB_T_ANT = simple_component_maker(lambda t,l,b,r:(r and not b,False,False,False)),
    RB_L_ANT = simple_component_maker(lambda t,l,b,r:(False,r and not b,False,False)),
    TR_L_ANT = simple_component_maker(lambda t,l,b,r:(False,t and not r,False,False)),
    TR_B_ANT = simple_component_maker(lambda t,l,b,r:(False,False,t and not r,False)),
    # Adjacent inputs, two outputs
    TL_BR_ANT = simple_component_maker(lambda t,l,b,r:(False,False,t and not l,t and not l)),
    LB_TR_ANT = simple_component_maker(lambda t,l,b,r:(l and not b,False,False,l and not b)),
    BR_TL_ANT = simple_component_maker(lambda t,l,b,r:(b and not r,b and not r,False,False)),
    RT_BL_ANT = simple_component_maker(lambda t,l,b,r:(False,r and not t,r and not t,False)),
    LT_BR_ANT = simple_component_maker(lambda t,l,b,r:(False,False,l and not t,l and not t)),
    BL_TR_ANT = simple_component_maker(lambda t,l,b,r:(b and not l,False,False,b and not l)),
    RB_TL_ANT = simple_component_maker(lambda t,l,b,r:(r and not b,r and not b,False,False)),
    TR_BL_ANT = simple_component_maker(lambda t,l,b,r:(False,t and not r,t and not r,False)),
)

DELAY_LOOPS = NamedTuple(
    L_R_1_DELAY = lambda x,y:MemoryComponent(x, y, lambda t,l,b,r:l, lambda s,t:(False,False,False,s and t==1), 1),
    L_R_2_DELAY = lambda x,y:MemoryComponent(x, y, lambda t,l,b,r:l, lambda s,t:(False,False,False,s and t==2), 2),
)