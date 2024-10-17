# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2022-, Sarang Bhagwat <sarangb2@illinois.edu>
# 
# This module is under the UIUC open-source license. See 
# github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE.txt
# for license details.
"""
Created on Mon Oct 14 15:33:50 2024

@author: sarangbhagwat
"""

from .. import ProcessBlock
from biosteam import System
from biorefineries.cellulosic.units import Saccharification
from biorefineries.cornstover import create_saccharification_system

__all__ = ('CellulosicEnzymaticSaccharification',)


class CellulosicEnzymaticSaccharification(ProcessBlock):
    
    def __init__(self, ID='cellulosic_enzymatic_saccharification'):
        create_function = get_cornstover_saccharification_system_full
        N_ins = 3
        N_outs = 1
        inlets = {i: 0 for i in ['pretreated cellulosic stream']}
        outlets = {'slurry: glucose, xylose':0}
        boiler = []
        wastewater = []
        ignored_HXN = []
        
        ProcessBlock.__init__(self, ID=ID, 
                     create_function=create_function, 
                     inlets=inlets, 
                     outlets=outlets,
                     boiler=boiler,
                     wastewater=wastewater,
                     ignored_HXN=ignored_HXN,
                     N_ins=N_ins,
                     N_outs=N_outs,
                     )


def get_cornstover_saccharification_system_full(ID='cornstover_saccharification_sys', ins=()):
    sys_upto_presacch = create_saccharification_system(ins=ins)
    sys_upto_presacch.simulate()
    R305 = Saccharification('R305', ins=sys_upto_presacch-0)
    cornstover_saccharification_sys = System.from_units('cornstover_saccharification_sys', 
                                                            sys_upto_presacch.units+[R305])
    
    return cornstover_saccharification_sys
