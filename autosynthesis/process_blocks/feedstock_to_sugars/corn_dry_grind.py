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
from biosteam import SolidsCentrifuge, System
from biorefineries.corn import create_system

__all__ = ('CornDryGrind',)

class CornDryGrind(ProcessBlock):
    
    def __init__(self, ID='corn_dry_grind', primary_inlet_name='corn'):
        self._primary_inlet_name = primary_inlet_name
        create_function = get_corn_system_upto_slurry
        base_TEA_year = 2018
        N_ins = 7
        N_outs = 3
        inlets = {'corn':6}
        outlets = {'slurry: glucose':1}
        boiler = [0]
        wastewater = [2]
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


def get_corn_system_upto_slurry(ID='corn_system_upto_slurry'):
    sys = create_system()
    sys.simulate()
    f = sys.flowsheet
    disconnect_outs_0_sink = [f.MX, f.P502, f.S1,
                              f.P304, # exclude ammonia addition
                              ]
    include_upstream_of = [f.P322]
    unit_set = set()
    for i in disconnect_outs_0_sink: i.outs[0].disconnect_sink()
    for i in include_upstream_of: 
        unit_set = unit_set.union(i.get_upstream_units())
        unit_set.add(i)
    unit_set.remove(f.E401)
    
    units_to_remove = list(f.E413.get_downstream_units().intersection(f.S1.get_upstream_units()))
    for i in units_to_remove: 
        try: unit_set.remove(i)
        except: pass
    
    f.V310-0-2-f.V321
    more_units_to_remove = [f.P407, f.E316, f.V317, f.P318,
                            f.V303, f.P304, # exclude ammonia addition
                            ]
    for i in more_units_to_remove: 
        try: unit_set.remove(i)
        except: pass
    
    # # include this heat exchanger if including ammonia addition; slurry has V>1 in some cases, leading to evaporator (F301) issues
    # H201 = bst.HXutility('H201', ins=f.P322-0, V=0., rigorous=True)
    # @H201.add_specification(run=False)
    # def H201_feed_vle_spec():
    #     H201_feed = H201.ins[0]
    #     H201_feed.vle(H=H201_feed.H, P=H201_feed.P)
    #     H201._run()
    # unit_set.add(H201)
    
    S201 = SolidsCentrifuge('S201', ins=f.P322-0, outs=('insoluble_proteins', 'slurry_to_fermentation_process'),
                                moisture_content=0.05,
                                split={'InsolubleProtein':0.85},
                                )
    unit_set.add(S201)
    
    corn_system_upto_slurry = System.from_units(ID, list(unit_set))
    for i in corn_system_upto_slurry.outs: i.disconnect_sink()
    # f.HX101.rigorous=True
    corn_system_upto_slurry.simulate(update_configuration=True)
    
    return corn_system_upto_slurry
