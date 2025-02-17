# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2022-, Sarang Bhagwat <sarangb2@illinois.edu>
# 
# This module is under the UIUC open-source license. See 
# github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE.txt
# for license details.
"""
Created on Mon Oct 14 16:22:31 2024

@author: sarangbhagwat
"""

from .. import ProcessBlock
from biorefineries.sugarcane import create_sucrose_fermentation_system

__all__ = ('FermentationEthanol',)

class FermentationEthanol(ProcessBlock):
    def __init__(self, ID='fermentation_ethanol', primary_inlet_name='juice: sucrose, glucose, fructose'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_sucrose_fermentation_system
        N_ins = 1
        N_outs = 3
        inlets = {i:0 for i in ['juice: sucrose, glucose, fructose', 
                                'slurry: glucose, xylose', 
                                'slurry: glucose',
                                'sugars: dextrose monohydrate']}
        outlets = {'broth: ethanol':0}
        boiler = []
        wastewater = [1]
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
