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
from biosteam import System, SystemFactory, Mixer, HeatUtility, StorageTank, Pump, ConveyingBelt, ChilledWaterPackage, HeatExchangerNetwork, create_high_rate_wastewater_treatment_system, main_flowsheet
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

#%% Generating units for storage of feed and product streams
def create_feed_and_product_storage_units(feeds, products, area=600,
                                 product_storage_tau=24.*7., # default to 1-week product storage
                                 include_empty_feeds=False,
                                 include_empty_products=False,
                                 wastewater_area=500,):
    units = []
    i = 1
    for feed in feeds:
        sink = feed.sink
        sink_index = sink.ins.index(feed)
        if (not feed.F_mol==0.) or include_empty_feeds:
            # print(feed.source, feed.ID, feed.sink)
            if is_solid(feed):
                str_num = str(area+i)
                pump_unit = Pump('P'+str_num, ins='', outs='', thermo=feed.thermo)
                pump_unit-0-sink_index-sink
                storage_unit = StorageTank('T'+str_num, ins=feed, thermo=feed.thermo)
                storage_unit-0-0-pump_unit
                units += [storage_unit, pump_unit]
                # storage_unit.ins[0].price = feed.price
                # feed.price = 0.
            elif is_liquid(feed) and not feed.imol['Water']/feed.F_mol==1:
                str_num = str(area+i)
                pump_unit = Pump('P'+str_num, ins='', outs='', thermo=feed.thermo)
                pump_unit-0-sink_index-sink
                storage_unit = StorageTank('T'+str_num, ins=feed, thermo=feed.thermo)
                storage_unit-0-0-pump_unit
                units += [storage_unit, pump_unit]
                # storage_unit.ins[0].price = feed.price
                # feed.price = 0.
            elif is_gaseous(feed):
                pass
            i+=1

    for product in products:
        # source = product.source
        # source_index = source.outs.index(product)
        if (not product.F_mol==0.) or include_empty_products:
            # print(product.source, product.ID, product.sink)
            if is_solid(product):
                str_num = str(area+i)
                storage_unit = StorageTank('T'+str_num, ins=product, tau=product_storage_tau, thermo=feed.thermo)
                pump_unit = Pump('P'+str_num, ins=storage_unit-0, thermo=feed.thermo)
                units += [storage_unit, pump_unit]
                pump_unit.outs[0].price = product.price
                product.price = 0.
            elif is_liquid(product) and not product.imol['Water']/product.F_mol==1\
                and not (is_from_unit_in_area(product, wastewater_area)): # as storage units are created only for no_facilities_sys, this condition is 
                                                                          # not really necessary (even though storage is created after WWT), might remove later
                str_num = str(area+i)
                storage_unit = StorageTank('T'+str_num, ins=product, tau=product_storage_tau, thermo=feed.thermo)
                pump_unit = Pump('P'+str_num, ins=storage_unit-0, outs='product_'+product.ID, thermo=feed.thermo)
                units += [storage_unit, pump_unit]
                pump_unit.outs[0].price = product.price
                product.price = 0.
            elif is_gaseous(product):
                pass
            i+=1
        
    return units
    
def is_from_unit_in_area(stream, area):
    source_ID = stream.source.ID
    # 3-digit area number
    if not source_ID[-4] in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']:
        if source_ID[-3]==str(area)[0]:
            return True
        else:
            return False
    # 4-digit area number
    else:
        if source_ID[-4]==str(area)[0] and source_ID[-3]==str(area)[1]:
            return True
        else:
            return False
    
def is_solid(stream, cutoff_massfrac=0.5):
    if stream.phase=='s':
        return True
    solid_phase_ref_chems = [i.ID for i in stream.chemicals if i.phase_ref=='s']
    if stream.F_mol and stream.imass[solid_phase_ref_chems].sum()/stream.F_mass>cutoff_massfrac:
        return True
    else:
        return False

def is_liquid(stream, cutoff_massfrac=0.5):
    liquid_phase_ref_chems = [i.ID for i in stream.chemicals if i.phase_ref=='l']
    if stream.F_mol and stream.imass[liquid_phase_ref_chems].sum()/stream.F_mass>cutoff_massfrac:
        return True
    else:
        return False

def is_gaseous(stream, cutoff_massfrac=0.5, cutoff_P=101325):
    if stream.phase=='g':
        return True
    gas_phase_ref_chems = [i.ID for i in stream.chemicals if i.phase_ref=='l']
    if stream.F_mol and stream.imass[gas_phase_ref_chems].sum()/stream.F_mass>cutoff_massfrac\
        and stream.P>=cutoff_P:
        return True
    else:
        return False

#%% Generating a system by process block-based synthesis

def get_system_block_based(feedstock, product, 
                           block_superstructure=None, 
                           choice=None, 
                           chemicals=None,
                           draw=True,
                           new_facilities=True,
                           new_storage=True,
                           storage_for_empty_feeds=False,
                           storage_for_empty_products=False,
                           TEA_year=2019):
    
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

    # Initialize and simulate no-facilities system; 
    # also update TEA year for all blocks
    units = []
    for i in all_blocks: 
        units+= list(i.system.units)
        i.TEA_year = TEA_year

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
    facilities_only_sys_units = []
    if new_facilities:
        facilities_only_sys = create_facilities_only_sys(wastewater_streams=wastewater_streams,
                                                         boiler_streams=boiler_streams, 
                                                         ignored_HXN_units=ignored_HXN_units)
        facilities_only_sys_units = facilities_only_sys.units
    
    # SystemFactory to initialize and connect storage units
    
    @SystemFactory(ID = 'storage_only_sys')
    def create_storage_only_sys(ins, outs, wastewater_streams=[], boiler_streams=[], ignored_HXN_units=[]):
        feeds = list(no_facilities_sys.feeds)
        products = list(no_facilities_sys.products)
        for i in wastewater_streams+boiler_streams: 
            if i in products: products.remove(i)
        feedstock_stream = all_blocks[0].inlet(feedstock)
        if feedstock_stream in feeds: feeds.remove(feedstock_stream)
        feed_storage_units = create_feed_and_product_storage_units(feeds, products,
                                                                   include_empty_feeds=storage_for_empty_feeds,
                                                                   include_empty_products=storage_for_empty_products,
                                                                   )
    
    # Create storage-only system
    storage_only_sys_units = []
    if new_storage:
        storage_only_sys = create_storage_only_sys(wastewater_streams=wastewater_streams,
                                                   boiler_streams=boiler_streams, 
                                                   ignored_HXN_units=ignored_HXN_units)
        storage_only_sys_units = storage_only_sys.units
    
    # Create full system
    full_sys = System.from_units('full_sys', 
                                 list(no_facilities_sys.units) + 
                                 facilities_only_sys_units +
                                 storage_only_sys_units)
    
    full_sys.simulate(update_configuration=True)
    if draw: full_sys.diagram('cluster')
    
    for i in range(3): full_sys.simulate()
    return full_sys

