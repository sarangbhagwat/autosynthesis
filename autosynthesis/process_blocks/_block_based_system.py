# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2022-, Sarang Bhagwat <sarangb2@illinois.edu>
# 
# This module is under the UIUC open-source license. See 
# github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE.txt
# for license details.
"""
Created on Mon Oct 14 17:51:28 2024

@author: sarangbhagwat
"""

import thermosteam as tmo
from biosteam import System, SystemFactory, Mixer, HeatUtility, ChilledWaterPackage, HeatExchangerNetwork, create_high_rate_wastewater_treatment_system, main_flowsheet
from biorefineries.cellulosic import create_facilities
from biorefineries.HP.chemicals_data import HP_chemicals
from biorefineries.TAL.chemicals_data import TAL_chemicals
from ._block_superstructure import BlockSuperstructure
# from biosteam.exceptions import UndefinedChemicalAlias

tmo_settings = tmo.settings
set_thermo = tmo_settings.set_thermo
Chemicals = tmo.Chemicals

#%% Consolidating multiple Chemicals/CompiledChemicals objects into a single CompiledChemicls object

def _get_consolidated_chemicals(list_of_compiled_chemicals):
    chems_brs_compiled = list_of_compiled_chemicals
    chems_brs = [Chemicals(cbr) for cbr in chems_brs_compiled]


    chems_flattened = Chemicals(chems_brs[0])
    chems_flattened.extend([i for i in chems_brs_compiled[0] if i not in chems_flattened])

    for i in range(1, len(chems_brs)):
        cbr = chems_brs[i]
        cbrc = chems_brs_compiled[i]
        # cbr.extend([i for i in cbrc if i not in cbr]) # add missing chemicals
        # print(chems_flattened, [i for i in cbrc if i not in chems_flattened])
        # chems_flattened.extend([i for i in cbrc if i not in chems_flattened])
        
        for i in cbrc:
            if i not in chems_flattened:
                append=True
                for j in chems_flattened:
                    if i.ID.lower() in [c.lower() for c in j.synonyms]:
                        append=False
                        break
                if append:
                    try:
                        chems_flattened.append(i)
                    except:
                        pass
                    

    chems_flattened.compile()

    # chems_flattened.set_alias('DiammoniumSulfate', '(NH4)2SO4')
    # chems_flattened.set_alias('DiammoniumSulfate', 'AmmoniumSulfate')

    for i in list(chems_brs_compiled[0].chemical_groups):
        chems_flattened.define_group(i, [c.ID for c in chems_brs_compiled[0].__dict__[i]])
    
    return chems_flattened

chemicals_default = _get_consolidated_chemicals([HP_chemicals, TAL_chemicals])

#%% Generating a system by process block-based synthesis

def get_system_block_based(feedstock, product, 
                           block_superstructure=None, 
                           choice=None, 
                           chemicals=None,
                           draw=True):
    
    if block_superstructure is None: block_superstructure = BlockSuperstructure()
    if chemicals is None: chemicals = chemicals_default
    # if not chemicals:
    #     chemicals = chems
    set_thermo(chemicals)
    
    u = main_flowsheet.unit
    BSS = block_superstructure
    BSS.create_graph()
    if draw: BSS.draw_graph()
    all_paths = BSS.get_all_paths(feedstock, product)
    if draw: BSS.get_and_draw_all_paths(feedstock, product)
    path = None
    
    if len(all_paths)>1: # more than one possible path
        if choice is None: # if user has not entered a choice of path
            print('\nMultiple paths possible; enter value for "choice" argument from the following integers:\n')
            for i in range(len(all_paths)):
                p = str(all_paths[i]).replace("'", "").replace("[", "").replace("]", "")
                print(f'{i}: {p}')
            return all_paths
        else:
            path = all_paths[choice]
    else:
        if not choice:
            path = all_paths[0] # only one possible path
    
    process_blocks = BSS.process_blocks
    process_block_keys = process_blocks.keys()
    all_blocks = []
    
    for p in path:
        if p in process_block_keys: 
            all_blocks.append(process_blocks[p])
    
    # Initialize and connect process blocks
    for b in all_blocks: b.create()
                
    for i in range(len(all_blocks)-1):
        all_blocks[i].make_all_possible_connections(all_blocks[i+1])
    
    # Initialize and simulate no-facilities system
    units = []
    for i in all_blocks: units+= list(i.system.units)
        
    no_facilities_sys = System.from_units('no_facilities_sys', units)
    no_facilities_sys.simulate(update_configuration=True)
    
    # SystemFactory to initialize and connect facilities
    
    @SystemFactory(ID = 'facilities_only_sys')
    def create_facilities_only_sys(ins, outs, wastewater_streams=[], boiler_streams=[], ignored_HXN_units=[]):
        # Wastewater treatment
        M501 = Mixer('M501', ins=wastewater_streams)
        
        @M501.add_specification(run=False)
        def M501_acid_base_removal_spec():
            for i in M501.ins:
                i.imol['NaOH','H2SO4'] = 0.
            M501._run()
        
        wastewater_treatment_sys = create_high_rate_wastewater_treatment_system(
            ins=M501-0, 
            area=500, 
            mockup=False,
            # skip_AeF=True,
            )
        
        tmo.settings.thermo.chemicals.set_synonym('BoilerChems', 'DAP')
        
        
        # Mix solid wastes to boiler turbogenerator
        M510 = Mixer('M510', ins=boiler_streams,
                                outs='wastes_to_boiler_turbogenerator')
        @M510.add_specification(run=True)
        def M510_spec():
            for i in M510.ins: i.phase='l'
            
        MX = Mixer(900, ['', ''])
        
        M503 = u.M503
        @M503.add_specification(run=False)
        def M503_spec():
            for i in M503.ins: i.phase='l'
            M503._run()
            for j in M503.outs: j.phase='l'
            
        # other facilities
        
        create_facilities(
            solids_to_boiler=M510-0,
            gas_to_boiler=wastewater_treatment_sys-1,
            process_water_streams=[
             i for i in no_facilities_sys.feeds if i.get_molar_fraction('Water')==1.
             ],
            feedstock=all_blocks[0].inlet(feedstock), #!!! may need to update later if adding feedstock handling outside process blocks
            RO_water=wastewater_treatment_sys-2,
            recycle_process_water=MX-0,
            BT_area=700,
            area=900,
        )
        
        # Chilled water processing
        CWP803 = ChilledWaterPackage('CWP803', agent=HeatUtility.cooling_agents[-2])
        
        # Heat exchanger network
        HXN = HeatExchangerNetwork('HXN1001',
                                    ignored=ignored_HXN_units,
                                    cache_network=False,
                                    )
        
        def HXN_no_run_cost():
            HXN.heat_utilities = []
            HXN._installed_cost = 0.
    
    # Get all streams to be diverted to wastewater treatment and boiler,
    # and all units to be ignored in HXN synthesis
    
    wastewater_streams = []
    boiler_streams = []
    ignored_HXN_units = []
    namespace_dict = {'u':u, 'ignored_HXN_units':ignored_HXN_units}
    for i in all_blocks: 
        wastewater_streams += [i.system.outs[j] for j in i.wastewater]
        boiler_streams += [i.system.outs[j] for j in i.boiler]
        for j in i.ignored_HXN:
            namespace_dict.update({'j':j})
            try:
                exec('ignored_HXN_units.append(u.' + j + ')', namespace_dict)
            except:
                breakpoint()
        
    # Create facilities-only system
    facilities_only_sys = create_facilities_only_sys(wastewater_streams=wastewater_streams,
                                                     boiler_streams=boiler_streams, 
                                                     ignored_HXN_units=ignored_HXN_units)
    
    # Create full system
    full_sys = System.from_units('full_sys', list(no_facilities_sys.units) + list(facilities_only_sys.units))
    full_sys.simulate(update_configuration=True)
    if draw: full_sys.diagram('cluster')
    
    for i in range(3): full_sys.simulate()
    return full_sys

