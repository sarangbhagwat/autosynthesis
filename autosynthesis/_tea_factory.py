# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2022-, Sarang Bhagwat <sarangb2@illinois.edu>
# 
# This module is under the UIUC open-source license. See 
# github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE.txt
# for license details.
"""
Created on Thu May  8 23:52:21 2025

@author: sarangbhagwat
"""
import biosteam as bst
from ._process_block import GDP_index, chem_index

__all__ = ('TEAFactory',)

CEPCI_by_year = bst.units.design_tools.cost_index.CEPCI_by_year

#%%
def BlockBasedTEA():
    
