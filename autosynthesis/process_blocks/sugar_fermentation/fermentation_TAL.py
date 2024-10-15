# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2022-, Sarang Bhagwat <sarangb2@illinois.edu>
# 
# This module is under the UIUC open-source license. See 
# github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE.txt
# for license details.
"""
Created on Mon Oct 14 16:38:28 2024

@author: sarangbhagwat
"""

from .. import ProcessBlock
from biorefineries.TAL.process_areas import create_TAL_fermentation_process

__all__ = ('FermentationTAL',)

class FermentationTAL(ProcessBlock):
    def __init__(self, ID='fermentation_TAL', primary_inlet_name='juice: sucrose, glucose, fructose'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_TAL_fermentation_process
        N_ins = 4
        N_outs = 4
        inlets = {primary_inlet_name:0}
        outlets = {'broth: TAL':1}
        boiler = []
        wastewater = [0]
        
        acceptable_in_edges=['juice: sucrose, glucose, fructose', 'slurry: glucose, xylose', 'slurry: glucose']
        out_edges=['broth: TAL']
        
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
