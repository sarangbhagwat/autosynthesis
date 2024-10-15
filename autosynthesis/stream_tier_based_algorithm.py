# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 00:13:45 2024

@author: sarangbhagwat
"""


tier1, tier2, tier3, tier4 = None, None, None, None

system_units = units = []

system = 1

# streams = system.streams

while True:
    WWT_mixer_ins = []
    boiler_mixer_ins = []
    for stream in system.streams:
        if tier1.test_criteria(stream):
            # link to best unit
            pass
        elif tier2.test_criteria(stream):
            # try to make tier 1
            pass
        elif tier3.test_criteria(stream):
            # try to make tier 2/1
            pass
        elif tier4.test_criteria(stream):
            # try to make tier 3/2/1 or send to WWT/boiler
            phases = stream.phases # can contain g, l, L, s # 15 combinations total (of n=4, r=1,2,3,4)
            
            if 'g' in phases:
                    if len(phases)==1: # 1: (g)
                        pc, useful = check_partial_condenser_for_tiers(stream=stream, tiers=(tier1, tier2, tier3))
                        if useful:
                            units.append(pc)
                        else:
                            if mostly_inorganics(stream):
                                vent = vent(stream)
                                units.append(vent)
                            else:
                                tc = total_condenser(stream)
                                WWT_mixer_ins.append(tc.outs[0])
                                units.append(tc)
                    elif len(phases)==2:
                        if ('l' or 'L') in phases: # 2: (g,l) or (g,L)
                            units.append(gas_liquid_phase_splitter(stream))
                        elif 's' in phases: # 1: (g,s)
                            units.append(gas_solid_phase_splitter(stream))
                    elif len(phases)==3:
                        if (('l' or 'L') and 's') in phases: # 2: (g,l,s) or (g,L,s)
                            units.append(gas_liquid_solid_phase_splitter(stream))
                        elif ('l' and 'L') in phases: # 1: (g,l,L)
                            units.append(gas_liquid_phase_splitter(stream))
                    elif len(phases)==4: # 1: (g,l,L,s)
                        units.append(gas_liquid_solid_phase_splitter(stream))
                
            elif ('l' or 'L') in phases: # 6: (l) or (L) or (l,L) or (l,s) or (L,s) or (l,L,s)
                total_solids = get_total_solids(stream)
                if total_solids>0.05:
                        centrifuge, useful = check_centrifuge_for_tiers(stream=stream, tiers=(tier1, tier2, tier3))
                        if useful:
                            units.append(centrifuge)
                        else:
                            if total_solids>0.4:
                                boiler_mixer_ins.append(stream)
                            else:
                                WWT_mixer_ins.append(stream)
                                
            elif 's' in phases: # 1: (s)
                boiler_mixer_ins.append(stream)
 
            else:
                raise RuntimeError
                    
        else:
            # vent or send to WWT/boiler
            pass
        
    # create a new system from system_units
    # create full system with system_units and facilities
    # simulate full system and cache connections and sustainability indicator value
    