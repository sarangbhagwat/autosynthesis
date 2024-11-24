# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2022-, Sarang Bhagwat <sarangb2@illinois.edu>
# 
# This module is under the UIUC open-source license. See 
# github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE.txt
# for license details.
"""
Created on Mon Oct 14 15:26:44 2024

@author: sarangbhagwat
"""

from .. import ProcessBlock
from biosteam import System, Unit, Mixer, Stream

__all__ = ('DextroseMonohydrateReceiving',)

class DextroseMonohydrateReceiving(ProcessBlock):
    
    def __init__(self, ID='dextrose_monohydrate_receiving',):
        create_function = create_dextrose_monohydrate_receiving_system
        N_ins = 7
        N_outs = 3
        inlets = {'dextrose monohydrate':0}
        outlets = {'sugars: dextrose monohydrate':0}
        boiler = []
        wastewater = []
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

def create_dextrose_monohydrate_receiving_system(ID):
    feedstock = Stream('dextrose_monoydrate', Glucose=1., Water=1., units='kmol/h')
    feedstock.price = 0.282524*0.909 # price is 2019$ # dextrose monohydrate stream is 90.9 wt% glucose
    feedstock.F_mass = 200_000 # initial value
    
    U101 = Unit('U101', ins=feedstock, outs='')
    @U101.add_specification(run=False)
    def U101_spec():
        U101.outs[0].copy_like(U101.ins[0])
    
    M201 = Mixer('M201', ins=(U101-0, ''), outs='') # bst.UnitGroup.get_material_cost uses bst.utils.get_inlet_origin; i.e., assumes source unit is a storage unit (i.e., attributes material cost to downstream unit) if len(source.ins) == len(source.outs) == 1 and 'processing' not in source.line.lower()
    
    return System.from_units(ID, [U101, M201])
