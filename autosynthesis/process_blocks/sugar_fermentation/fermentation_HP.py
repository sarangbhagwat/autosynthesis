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
from biorefineries.HP.process_areas import create_HP_fermentation_process

__all__ = ('FermentationHP',)

class FermentationHP(ProcessBlock):
    def __init__(self, ID='fermentation_HP', primary_inlet_name='slurry: glucose'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_HP_fermentation_process
        N_ins = 7
        N_outs = 4
        inlets = {primary_inlet_name:0}
        outlets = {'broth: 3-HP':0}
        boiler = []
        wastewater = [2, 3]
        
        acceptable_in_edges=['juice: sucrose, glucose, fructose', 'slurry: glucose, xylose', 'slurry: glucose']
        out_edges=['broth: 3-HP']
        
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
