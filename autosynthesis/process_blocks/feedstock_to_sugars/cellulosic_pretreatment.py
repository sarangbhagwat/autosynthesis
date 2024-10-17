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
from biorefineries.cornstover import create_dilute_acid_pretreatment_system

__all__ = ('CellulosicDiluteAcidPretreatment',)

class CellulosicDiluteAcidPretreatment(ProcessBlock):
    
    def __init__(self, ID='cellulosic_dilute_acid_pretreatment'):
        create_function = create_dilute_acid_pretreatment_system
        N_ins = 3
        N_outs = 2
        inlets = {i: 0 for i in ['corn stover', 'miscanthus', 'switchgrass', 'wheat straw']}
        outlets = {'pretreated cellulosic stream':0}
        boiler = []
        wastewater = [1]
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

