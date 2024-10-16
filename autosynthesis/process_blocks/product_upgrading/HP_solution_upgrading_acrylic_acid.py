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
from biorefineries.HP.process_areas import create_HP_to_acrylic_acid_upgrading_process

__all__ = ('HPSolutionUpgradingAcrylicAcid',)

class HPSolutionUpgradingAcrylicAcid(ProcessBlock):
    def __init__(self, ID='HP_solution_upgrading_acrylic_acid', primary_inlet_name='3-HP solution'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_HP_to_acrylic_acid_upgrading_process
        N_ins = 4
        N_outs = 6
        inlets = {'3-HP solution':0}
        outlets = {'glacial acrylic acid':0}
        boiler = []
        wastewater = [2]
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
