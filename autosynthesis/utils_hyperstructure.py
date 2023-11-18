# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 18:18:45 2023

@author: sarangbhagwat
"""

def get_hyperstructure(systems_dict, 
                       streams_dict, 
                       first_mixer_ID='M601', 
                       first_splitter_ID='S601',):
    
    # Inter-system mixers and splitters
    mixers_and_splitters = get_inter_system_mixers_and_splitters(systems_dict, 
                                                                 streams_dict, 
                                                                 first_mixer_ID, 
                                                                 first_splitter_ID)
    
    # # Storage 
    # storage_sys = create_storage_dict(systems_dict,
    #                                   streams_dict)
    
    # Facilities
    facilities_sys = create_facilities_sys(systems_dict, 
                                           streams_dict)
           
    hyperstructure = Hyperstructure(systems_dict, mixers_and_splitters, facilities_sys,)
    
    return hyperstructure

class Hyperstructure(AgileSystem):
    pass

def stream_type(stream, 
                product_criteria,  
                solid_waste_criteria = [lambda s: s.imass['Water']/s.F_mass < 0.5],
                liquid_waste_criteria = [lambda s: s.imass['Water']/s.F_mass > 0.5],
                vent_criteria = [lambda s: s.phase=='g']):
    stream_type = 0
    return stream_type

def get_inter_system_mixers_and_splitters(systems_dict, 
                                          streams_dict, 
                                          first_mixer_ID, 
                                          first_splitter_ID):
    mixer_ID_letter, splitter_ID_letter = first_mixer_ID[:1], first_splitter_ID[:1]
    mixer_ID_number, splitter_ID_number = int(first_mixer_ID[1:]), int(first_splitter_ID[1:])
    
    mixers, splitters = {}, {}
    
    prev_area = None
    for area, streams in streams_dict.items():
        
        mixers[area], splitters[area] = [], []
        
        main_ins = streams_dict[area]['main input streams']
        main_outs = streams_dict[area]['main output streams']
        solid_wastes = streams_dict[area]['solid waste streams']
        liquid_wastes = streams_dict[area]['liquid waste streams']
        vents = streams_dict[area]['vent streams']
        
        n_splits = len(systems_dict[area]) + 1
    
        if prev_area:
            splitters_from_prev_area = splitters[prev_area]
            mixer_splitter_combos = create_mixer_splitter_combo_for_each_system(systems_dict[area], splitters_from_prev_area)
        create_output_splitters_for_system(area, systems_dict[area])
        if prev_area:
            for s in main_ins:
                mixer = create_mixer(ID=mixer_ID_letter+str(mixer_ID_number),
                                     ins=(splitter[1] for splitter in splitters[prev_area]),
                                     outs=(s,))
                mixer_ID_number += 1
                mixers[area].append(mixer)
        
        for s in main_outs:
            splitter = create_splitter(ID=splitter_ID_letter+str(splitter_ID_number),
                                       ins=s,
                                       N_outs=n_splits)
            splitter_ID_number += 1
            splitters[area].append(splitter)
        
        mixer = create_mixer(ID=mixer_ID_letter+str(mixer_ID_number),
                             ins=(splitter[0] for splitter in splitters))
        mixer_ID_number += 1
        mixers[area].append(mixer)
        
        splitter = create_splitter(ID=splitter_ID_letter+str(splitter_ID_number),
                                   ins=mixer-0,
                                   N_outs=n_splits)
        
        splitter_ID_number += 1
        splitters[area].append(splitter)
        
        prev_area = area
        
        