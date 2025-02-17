# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2022-, Sarang Bhagwat <sarangb2@illinois.edu>
# 
# This module is under the UIUC open-source license. See 
# github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE.txt
# for license details.
"""
Created on Mon Oct 14 16:47:57 2024

@author: sarangbhagwat
"""

from .. import ProcessBlock
from biorefineries.ethanol import create_ethanol_purification_system

__all__ = ('EthanolSeparation',)

class EthanolSeparation(ProcessBlock):
    def __init__(self, ID='ethanol_separation', primary_inlet_name='broth: ethanol'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_ethanol_purification_system
        N_ins = 2
        N_outs = 3
        inlets = {'broth: ethanol':0}
        outlets = {'ethanol':0}
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
