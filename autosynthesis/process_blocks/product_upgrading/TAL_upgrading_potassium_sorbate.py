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
        inlets = {primary_inlet_name:0}
        outlets = {'potassium sorbate':0}
        boiler = [1]
        wastewater = [6, 7]
        
        acceptable_in_edges=['TAL', 'TAL solution']
        out_edges=['potassium sorbate']
        
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


class TALUpgradingTHFEthanolPotassiumSorbate(ProcessBlock):
    def __init__(self, ID='TAL_upgrading_THF_ethanol_potassium_sorbate', primary_inlet_name='TAL'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_TAL_to_sorbic_acid_upgrading_process_THF_Ethanol
        N_ins = 8
        N_outs = 10
        inlets = {primary_inlet_name:0}
        outlets = {'potassium sorbate':0}
        boiler = [1]
        wastewater = [7, 8, 9]
        
        acceptable_in_edges=['TAL', 'TAL solution']
        out_edges=['potassium sorbate']
        
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
