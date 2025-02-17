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
from biorefineries.TAL.process_areas import create_TAL_separation_solubility_exploit_process
from biosteam import System, Splitter, HXutility

__all__ = ('TALHotSeparation', 'TALCooledSeparation')

class TALHotSeparation(ProcessBlock):
    def __init__(self, ID='TAL_hot_separation', primary_inlet_name='broth: TAL'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_TAL_separation_solubility_exploit_process
        base_TEA_year = 2019
        N_ins = 4
        N_outs = 6
        inlets = {'broth: TAL':0}
        outlets = {'hot TAL':4}
        boiler = [1]
        wastewater = [2, 3, 5]
        ignored_HXN = ['H401', 'C401']
        
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

class TALCooledSeparation(ProcessBlock):
    def __init__(self, ID='TAL_cooled_separation', primary_inlet_name='broth: TAL'):
        self._primary_inlet_name = primary_inlet_name
        create_function = create_TAL_cooled_separation_solubility_exploit_process
        base_TEA_year = 2019
        N_ins = 6
        N_outs = 9
        inlets = {'broth: TAL':3}
        outlets = {'TAL':8}
        boiler = [0]
        wastewater = [1, 2, 7]
        ignored_HXN = ['H401', 'C401', 'S403', 'H420']
        
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

def create_TAL_cooled_separation_solubility_exploit_process(ID='TAL_cooled_separation'):
    sys = create_TAL_separation_solubility_exploit_process()
    sys.simulate()
    f = sys.flowsheet
    # at the baseline, no evaporator before recycle as heating would decarboxylate TAL
    S403 = Splitter('S403', 
                        ins=sys-2, # recycled supernatant, with or without evaporation
                        outs=('S403_recycled_supernatant', 'S403_to_WWT'),
                        split=0., # optimal split=0.
                        )
    
    @S403.add_specification(run=False)
    def S403_spec():
        S403._run()
        for i in S403.outs: i.phase = 'l'
    S403-0-2-sys
    
    H420 = HXutility('H420', 
                         ins=sys-4, # solid TAL
                         outs='cooled_solid_TAL', 
                         T=273.15+25.,)
    
    
    TAL_cooled_separation_sys = System.from_units(ID, list(sys.units) + [H420, S403])
    TAL_cooled_separation_sys.simulate(update_configuration=True)
    
    return TAL_cooled_separation_sys
