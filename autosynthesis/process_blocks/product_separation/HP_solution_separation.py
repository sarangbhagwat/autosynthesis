# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2022-, Sarang Bhagwat <sarangb2@illinois.edu>
# 
# This module is under the UIUC open-source license. See 
# github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE.txt
# for license details.
"""
Created on Mon Oct 14 16:17:27 2024

@author: sarangbhagwat
"""

from .. import ProcessBlock
from biorefineries.HP.process_areas import create_HP_separation_improved_process

__all__ = ('HPSolutionSeparation',)

class HPSolutionSeparation(ProcessBlock):
    def __init__(self, ID='HP_solution_separation', primary_inlet_name='broth: 3-HP'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_HP_separation_improved_process
        N_ins = 6
        N_outs = 4
        inlets = {'broth: 3-HP':0}
        outlets = {'3-HP solution':0}
        boiler = [1]
        wastewater = [3, 4, 5, 6]
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
