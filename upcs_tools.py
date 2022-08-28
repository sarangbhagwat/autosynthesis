# -*- coding: utf-8 -*-
"""
Created on Sat Jan 16 19:09:17 2021

@author: sarangbhagwat
"""
# %% Imports and chemicals initialization

import numpy as np
from pandas import DataFrame
import pdb
import thermosteam as tmo
import biosteam as bst
# import copy 
from copy import deepcopy
from inspect import getmembers
from matplotlib import pyplot as plt
from biorefineries.TAL.chemicals_data import TAL_chemicals as chems
from biorefineries.TAL import units
from biorefineries.TAL.system_solubility_exploit import f, u, s, get_SA_MPSP

#%% Set default feasible and minimal components for all units
for unit in u:
    unit._feasibles = set([i.ID for i in chems])
    unit._minimals = set()
    unit._maximals = set()
    if isinstance(unit, units.Reactor) or isinstance(unit, units.CoFermentation):
        print(unit.ID)
        # for k in unit.__dict__.keys():
        for m in getmembers(unit):
            k = m[0]
            if '_rxns' in k:
                rxns = m[1]
                print(k)
                for rxn in rxns:
                    print(rxn.reactant)
                    unit._minimals.add(rxn.reactant)
                    
#%% Manually add additional minimal or feasible components for any units
pdb.set_trace()
