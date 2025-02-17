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
from biorefineries.HP.process_areas import create_HP_separation_improved_process, create_HP_separation_hexanol_extraction_process

__all__ = ('HPSolutionSeparationIExCR', 'HPSolutionSeparationHexanol')

class HPSolutionSeparationIExCR(ProcessBlock):
    def __init__(self, ID='HP_solution_separation_IEx_CR', primary_inlet_name='broth: 3-HP'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_HP_separation_improved_process
        base_TEA_year = 2016
        N_ins = 6
        N_outs = 7
        inlets = {'broth: 3-HP':0}
        outlets = {'3-HP solution':0}
        boiler = [1]
        wastewater = [3, 4, 5, 6]
        ignored_HXN = []
        
        ProcessBlock.__init__(self, ID=ID, 
                     create_function=create_function, 
                     base_TEA_year=base_TEA_year,
                     inlets=inlets, 
                     outlets=outlets,
                     boiler=boiler,
                     wastewater=wastewater,
                     ignored_HXN=ignored_HXN,
                     N_ins=N_ins,
                     N_outs=N_outs,
                     )

class HPSolutionSeparationHexanol(ProcessBlock):
    def __init__(self, ID='HP_solution_separation_hexanol', primary_inlet_name='broth: 3-HP'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_HP_separation_hexanol_extraction_process
        base_TEA_year = 2016
        N_ins = 3
        N_outs = 5
        inlets = {'broth: 3-HP':0}
        outlets = {'3-HP solution':0}
        boiler = [1]
        wastewater = [3, 4,]
        ignored_HXN = []
        
        ProcessBlock.__init__(self, ID=ID, 
                     create_function=create_function, 
                     base_TEA_year=base_TEA_year,
                     inlets=inlets, 
                     outlets=outlets,
                     boiler=boiler,
                     wastewater=wastewater,
                     ignored_HXN=ignored_HXN,
                     N_ins=N_ins,
                     N_outs=N_outs,
                     )
        