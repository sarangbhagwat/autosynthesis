# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2022-, Sarang Bhagwat <sarangb2@illinois.edu>
# 
# This module is under the UIUC open-source license. See 
# github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE.txt
# for license details.
"""
Created on Mon Oct 14 16:52:34 2024

@author: sarangbhagwat
"""

from .. import ProcessBlock
from biorefineries.TAL.process_areas import create_TAL_separation_solubility_exploit_process

__all__ = ('TALSeparation',)

class TALSeparation(ProcessBlock):
    def __init__(self, ID='TAL_separation', primary_inlet_name='broth: TAL'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_TAL_separation_solubility_exploit_process
        N_ins = 4
        N_outs = 6
        inlets = {primary_inlet_name:1}
        outlets = {'TAL':4}
        boiler = [1]
        wastewater = [2, 3, 5]
        
        acceptable_in_edges=['broth: TAL']
        out_edges=['TAL']
        
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
