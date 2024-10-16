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
from biorefineries.cornstover import create_dilute_acid_pretreatment_system, create_saccharification_system

__all__ = ('CellulosicPretreatmentSaccharification',)

class CellulosicPretreatmentSaccharification(ProcessBlock):
    
    def __init__(self, ID='cellulosic_pretreatment_saccharification', primary_inlet_name='corn stover'):
        self._primary_inlet_name = primary_inlet_name
        create_function = get_cornstover_pretreatment_saccharification
        N_ins = 9
        N_outs = 2
        inlets = {i: 0 for i in ['corn stover', 'miscanthus', 'switchgrass', 'wheat straw']}
        outlets = {'slurry: glucose, xylose':1}
        boiler = []
        wastewater = [0]
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


def get_cornstover_pretreatment_saccharification(ID='cornstover_pretreatment_saccharification'):
    cornstover_pretreatment_sys = create_dilute_acid_pretreatment_system('cornstover_pretreatment_sys')
    
    cornstover_saccharification_sys = get_cornstover_saccharification_system_full(ID='cornstover_saccharification_sys',
                                                                     ins=(cornstover_pretreatment_sys-0))
    
    cornstover_pretreatment_sys.simulate(update_configuration=True)
    cornstover_saccharification_sys.simulate(update_configuration=True)
    
    cornstover_pretreatment_saccharification = System.from_units(ID, 
                                                                 list(cornstover_pretreatment_sys.units) +
                                                                 list(cornstover_saccharification_sys.units))

    return cornstover_pretreatment_saccharification


def get_cornstover_saccharification_system_full(ID='cornstover_saccharification_sys', ins=()):
    sys_upto_presacch = create_saccharification_system(ins=ins)
    sys_upto_presacch.simulate()
    R305 = Saccharification('R305', ins=sys_upto_presacch-0)
    cornstover_saccharification_sys = System.from_units('cornstover_saccharification_sys', 
                                                            sys_upto_presacch.units+[R305])
    
    return cornstover_saccharification_sys
