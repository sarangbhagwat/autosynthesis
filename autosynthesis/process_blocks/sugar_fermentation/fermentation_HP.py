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
        base_TEA_year = 2016
        N_ins = 7
        N_outs = 4
        inlets = {i:0 for i in ['juice: sucrose, glucose, fructose', 
                                'slurry: glucose, xylose',
                                'slurry: glucose',
                                'sugars: dextrose monohydrate']}
        outlets = {'broth: 3-HP':0}
        boiler = []
        wastewater = [2, 3]
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
