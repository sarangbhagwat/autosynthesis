# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2022-, Sarang Bhagwat <sarangb2@illinois.edu>
# 
# This module is under the UIUC open-source license. See 
# github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE.txt
# for license details.
"""
Created on Mon Oct 14 17:04:04 2024

@author: sarangbhagwat
"""

from .. import ProcessBlock
from biorefineries.TAL.process_areas import create_TAL_to_sorbic_acid_upgrading_process, create_TAL_to_sorbic_acid_upgrading_process_THF_Ethanol

__all__ = ('TALUpgradingIPAPotassiumSorbate',)


class TALUpgradingIPAPotassiumSorbate(ProcessBlock):
    def __init__(self, ID='TAL_upgrading_IPA_potassium_sorbate', primary_inlet_name='TAL'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_TAL_to_sorbic_acid_upgrading_process
        N_ins = 7
        N_outs = 8
        inlets = {i:0 for i in ['TAL', 'TAL solution']}
        outlets = {'potassium sorbate':0}
        boiler = [1]
        wastewater = [6, 7]
        ignored_HXN = ['u.R401', 'u.R402', 'u.R403']
        
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


class TALUpgradingTHFEthanolPotassiumSorbate(ProcessBlock):
    def __init__(self, ID='TAL_upgrading_THF_ethanol_potassium_sorbate', primary_inlet_name='TAL'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_TAL_to_sorbic_acid_upgrading_process_THF_Ethanol
        N_ins = 8
        N_outs = 10
        inlets = {i:0 for i in ['TAL', 'TAL solution']}
        outlets = {'potassium sorbate':0}
        boiler = [1]
        wastewater = [7, 8, 9]
        ignored_HXN = ['u.R401', 'u.R402', 'u.R403']
        
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