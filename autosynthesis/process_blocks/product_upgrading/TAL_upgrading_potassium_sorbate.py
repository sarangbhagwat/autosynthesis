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

__all__ = ('TALUpgradingIPAPotassiumSorbate', 'TALUpgradingTHFEthanolPotassiumSorbate')


class TALUpgradingIPAPotassiumSorbate(ProcessBlock):
    def __init__(self, ID='TAL_upgrading_IPA_potassium_sorbate', primary_inlet_name='TAL'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_TAL_to_sorbic_acid_upgrading_process
        base_TEA_year = 2019
        N_ins = 7
        N_outs = 8
        inlets = {i:0 for i in ['hot TAL', 'TAL solution', 'TAL']}
        outlets = {'potassium sorbate':0}
        boiler = [1]
        wastewater = [6, 7]
        ignored_HXN = ['R401', 'R402', 'R403']
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


class TALUpgradingTHFEthanolPotassiumSorbate(ProcessBlock):
    def __init__(self, ID='TAL_upgrading_THF_ethanol_potassium_sorbate', primary_inlet_name='TAL'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_TAL_to_sorbic_acid_upgrading_process_THF_Ethanol
        base_TEA_year = 2019
        N_ins = 8
        N_outs = 10
        inlets = {i:0 for i in ['hot TAL', 'TAL solution', 'TAL']}
        outlets = {'potassium sorbate':0}
        boiler = [1]
        wastewater = [7, 8, 9]
        ignored_HXN = ['R401', 'R402', 'R403']
        
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
