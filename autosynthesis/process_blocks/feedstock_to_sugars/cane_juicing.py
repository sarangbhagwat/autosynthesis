# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2022-, Sarang Bhagwat <sarangb2@illinois.edu>
# 
# This module is under the UIUC open-source license. See 
# github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE.txt
# for license details.
"""
Created on Mon Oct 14 15:02:24 2024

@author: sarangbhagwat
"""

from .. import ProcessBlock
from biorefineries.sugarcane import create_juicing_system_up_to_clarification

__all__ = ('SugarcaneJuicing',)

class SugarcaneJuicing(ProcessBlock):
    
    def __init__(self, ID='sugarcane_juicing', primary_inlet_name='sugarcane'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_juicing_system_up_to_clarification
        N_ins = 4
        N_outs = 2
        inlets = {primary_inlet_name:0}
        outlets = {'juice: sucrose, glucose, fructose':0}
        boiler = [1]
        wastewater = []
        
        acceptable_in_edges=['sugarcane', 'sweet sorghum']
        out_edges=['juice: sucrose, glucose, fructose']
        
        ProcessBlock.__init__(self, ID=ID, 
                     create_function=create_function, 
                     inlets=inlets, 
                     outlets=outlets,
                     boiler=boiler,
                     wastewater=wastewater,
                     N_ins=N_ins,
                     N_outs=N_outs,
                     acceptable_in_edges=acceptable_in_edges,
                     out_edges=out_edges,
                     )
