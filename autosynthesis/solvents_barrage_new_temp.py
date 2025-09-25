# -*- coding: utf-8 -*-
# Copyright (C) 2022-2025, Sarang Bhagwat
# 
# This module is under the UIUC open-source license. See 
# github.com/BioSTEAMDevelopmentGroup/biosteam/blob/master/LICENSE.txt
# for license details.
"""
Created on Tue Sep  2 23:35:48 2025

@author: saran
"""
# %% Imports and setup
import thermosteam as tmo
import biosteam as bst
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt    
from datetime import datetime

from autosynthesis.distillation_train import get_distillation_superstructure, get_all_possible_distillation_trains, TargetProduct, TargetProductsSet

plot = False

#%%

def is_at_least_biphase(stream):
    phases = stream.phases
    
    # if not at least biphase, return 0
    if len(phases)<2:
        return False
    
    n_phases_with_flow = 0
    for p in phases:
        if stream[p].F_mol > 0.0: n_phases_with_flow += 1
    if n_phases_with_flow<2:
        return False
    
    return True

def get_primary_phase(chem_ID, stream):
    max_mol = 0
    primary_phase = None
    for p in stream.phases:
        curr_mol = stream[p].imol[chem_ID]
        if curr_mol > max_mol:
            max_mol = curr_mol
            primary_phase = p
    return primary_phase

def get_K(chem_ID, stream, phase_1, phase_2):
    return (stream[phase_1].imol[chem_ID]/stream[phase_1].F_mol)/max(1e-6, (stream[phase_2].imol[chem_ID]/stream[phase_2].F_mol))

def get_K_extract_over_raffinate(solute_ID, stream, solvent_ID, carrier_ID):
    if not is_at_least_biphase(stream): return 0.0
        
    extract_phase = get_primary_phase(solvent_ID, stream)
    # other_phase = 'l' if extract_phase=='L' else 'L'
    raffinate_phase = get_primary_phase(carrier_ID, stream)
    if extract_phase==raffinate_phase: return 0.0
    
    return get_K(solute_ID, stream, extract_phase, raffinate_phase)

def get_conc_factor(solute_ID, solvent_ID, mixed, feed):
    if not is_at_least_biphase(mixed): return 0.0
    extract_phase = get_primary_phase(solvent_ID, mixed)
    extract = mixed[extract_phase]
    return (extract.imol[solute_ID]/extract.F_mol)/(feed.imol[solute_ID]/feed.F_mol)

def get_fraction_extracted(solute_ID, stream, solvent_ID, carrier_ID):
    if not is_at_least_biphase(stream): return 0.0
        
    extract_phase = get_primary_phase(solvent_ID, stream)
    # other_phase = 'l' if extract_phase=='L' else 'L'
    raffinate_phase = get_primary_phase(carrier_ID, stream)
    if extract_phase==raffinate_phase: return 0.0

    return max(0.0, stream[extract_phase].imol[solute_ID]/stream.imol[solute_ID])

# def simulate_and_get_metrics(solute_ID, stream, solvent_ID, carrier_ID, feed,
#                             metrics=[get_conc_factor, get_fraction_extracted]):
#     stream.phase = 'l'
#     stream.imol[solvent_ID] = 1000
#     stream.lle(T=stream.T)
    
#     metric_vals = [metric(solute_ID, stream, solvent_ID, carrier_ID, feed) for metric in metrics]
#     stream.phase = 'l'
#     stream.imol[solvent] = 0
    
#     return metric_vals

#%% Default solvent IDs list
solvent_IDs = [
                'Pentadecanol',
                'Tridecanol',
                'Ethanol',
                'Methanol',
                'Ethyl acetate',
                'Isopentyl acetate',
                'Propyl acetate',
                'Butyl acetate',
                'Diethyl ether',
                'Methyl isobutyl ketone',
                'Butanol',
                '1,4-Butanediol',
                'Hexanol',
                'Hexane',
                'Cyclopentanol',
                'Cyclohexanol',
                'Cyclohexanone',
                'Heptanol',
                'Octanol',
                '1,8-Octanediol',
                '2-Ethyl hexanol',
                'Nonanol',
                'Decanol',
                'Dodecanol',
                '117-81-7', # CAS number for Dioctyl (Diethylhexyl) phthalate
                'Diethyl sebacate',
                # 'Glycerol',
                'Toluene',
                'Trioctylamine',
                'Isoamyl alcohol',
                # '5137-55-3', # CAS number for Aliquat 336
                # 'Water',
                'Benzene',
                '143-28-2', # CAS number for Oleyl alcohol
                'Tetrahydrofuran',
                ]

#%% Load chemicals and set solute and carrier
from nskinetics.data.P_putida_all_metabolites import load_putida_chems

#%% P. putida metabolites
# file_path = 'C:/Users/saran/Documents/Academia/repository_clones/nskinetics/nskinetics/tests/local_only/metabolites/data/putida_SMILES.txt'
# chems = load_putida_chems()

#%% Y.lipolytica metabolites
file_path = 'C:/Users/saran/Documents/Academia/repository_clones/nskinetics/nskinetics/data/metabolites_Y-lipolityca-CLIB122.txt'  # Replace with your file name

with open(file_path, 'r') as file:
    lines = file.readlines()

# Strip newline characters from each line
string_list = [line.strip() for line in lines]

print(string_list)

chems = tmo.Chemicals([])
for cID in string_list:
    try:
        c = tmo.Chemical(cID)
        if c.Dortmund and (c.Tb is not None) and c.Hvap and c.Psat:
            chems.append(c)
    except:
        pass
    # chems = [tmo.Chemical(c) for c in string_list]

#%%
secondary_metabolites = [c.ID for c in chems]

if 'oxidane' in secondary_metabolites:
    secondary_metabolites.remove('oxidane') # Water

if 'isobutanol' in secondary_metabolites:
    secondary_metabolites.remove('isobutanol') # Water
    
else:
    chems.append(tmo.Chemical('Water'))
# solute = '3-hydroxy-2,2-dimethylbutanoic acid' # 29269-83-8
# solute = '3-hydroxybutanoic acid'
solute = 'Isobutanol'
carrier = 'Water'

chems.append(tmo.Chemical(solute))
chems.append(tmo.Chemical(carrier))

for si in solvent_IDs:
    chems.append(tmo.Chemical(si))
chems.compile()

tmo.settings.set_thermo(chems)

# if 'oxidane' in secondary_metabolites:
#     chems.set_synonym('oxidane', 'Water')
    
chems.set_synonym('117-81-7', 'Diethylhexyl pthalate')
chems.set_synonym('143-28-2', 'Oleyl alcohol')

#%% Create streams and set solute and carrier
original_stream = tmo.Stream('original_stream', T=273.15+25)

# for c in chems:
#     s1.imol[c.ID] = 10


original_stream.imol[solute] = 50
original_stream.imol[carrier] = 5000

mixed_stream = original_stream.copy(ID='mixed_stream')
mixed_stream.lle(T=mixed_stream.T)

#%% Test all solvents
conc_factors_solvents = []
frac_extracted_solvents = []

all_candidate_solvents = solvent_IDs + secondary_metabolites
for solvent in all_candidate_solvents:
    mixed_stream.phase = 'l'
    mixed_stream.imol[solvent] = 1000
    mixed_stream.lle(T=mixed_stream.T)
    
    conc_factors_solvents.append(get_conc_factor(solute, solvent, mixed_stream, original_stream))
    frac_extracted_solvents.append(get_fraction_extracted(solute, mixed_stream, solvent, carrier))
    
    mixed_stream.phase = 'l'
    mixed_stream.imol[solvent] = 0

solvents_df = pd.DataFrame.from_dict({'Solvent': all_candidate_solvents, 
                                      'Conc factor': conc_factors_solvents,
                                      'Frac extracted':frac_extracted_solvents})

solvents_df = solvents_df.sort_values(by='Frac extracted', ascending=False)

#%%
if plot:
    ax = solvents_df.plot.bar(x='Solvent', rot=90, figsize=(20,10))
    xtick_labels = ax.get_xticklabels()
    for label in xtick_labels:
        if label.get_text() in secondary_metabolites:
            label.set_color('green')
    
    plt.show()
    
#%% Set best solvent (extractant)

# best_solvent = list(solvents_df['Solvent'])[2]
# best_solvent = 'Ethyl acetate'
best_solvent = 'Isopentyl acetate'
solvent_stream = tmo.Stream('solvent_stream', T=273.15+25)
solvent_stream.imol[best_solvent] = 1000

#%% Load (mix in) best solvent
mixed_stream.mix_from([original_stream, solvent_stream])
mixed_stream.lle(T=mixed_stream.T)

#%% Get obj with other metabolites present

imol_range_metabolites = np.linspace(0., 100, 10)

conc_factors_with_metabolites = {}
frac_extracted_with_metabolites = {}

max_obj = 0.0
best_metabolite = None

extraction_improving_metabolites = []

for m in secondary_metabolites:
    # if m==best_solvent:
    #     continue
    conc_factors_with_metabolites[m] = []
    frac_extracted_with_metabolites[m] = []
    for i in imol_range_metabolites:
        mixed_stream.phase = 'l'
        mixed_stream.imol[m] += i
        try:
            mixed_stream.lle(T=mixed_stream.T)
            conc_factors_with_metabolites[m].append(get_conc_factor(solute, best_solvent, mixed_stream, original_stream))
            frac_extracted_with_metabolites[m].append(get_fraction_extracted(solute, mixed_stream, best_solvent, carrier))
        except:
            breakpoint()
        
        mixed_stream.phase = 'l'
        if m==best_solvent:
            mixed_stream.imol[m] -= i
        else:
            mixed_stream.imol[m] = 0
        if np.any(np.array(mixed_stream.mol)<0): 
            breakpoint()
            
    if round(max(frac_extracted_with_metabolites[m]), 3)\
        > round(frac_extracted_with_metabolites[m][0], 3):
        extraction_improving_metabolites.append(m)
        
    if max(frac_extracted_with_metabolites[m]) > max_obj:
        max_obj = max(frac_extracted_with_metabolites[m])
        best_metabolite = m
    
#%% Plot
if plot:
    for k,v in conc_factors_with_metabolites.items():
        plt.plot(imol_range_metabolites, v)
        plt.xlim(0)
        plt.ylim(0)
        plt.xlabel(f'mol {k}')
        plt.ylabel(f'Conc factor for {solute} (conc in extract : conc in feed')
        plt.show()
    
    for k,v in frac_extracted_with_metabolites.items():
        plt.plot(imol_range_metabolites, v)
        plt.xlim(0)
        plt.ylim(0,1)
        plt.xlabel(f'mol {k}')
        plt.ylabel(f'Frac of {solute} extracted')
        plt.show()
    

#%% Simulate extraction without other metabolites

MSMS1 = bst.MultiStageMixerSettlers('MSMS1', 
                                    ins=(original_stream, solvent_stream), 
                                    outs=('extract', 'raffinate'), N_stages=5,
                                    top_chemical=best_solvent,
                                    )

# @MSMS1.add_specification()
# def MSMS1_spec():
#     pass

MSMS1.simulate()

MSMS1.show(N=100)

#%% Add a distillation train

# Get distillation superstructure
dist_ss = get_distillation_superstructure(MSMS1.extract)
dist_ss.system.diagram('cluster')

# Define target products set
solvent_product = TargetProduct('solvent_product',
                                criteria = [lambda s: s.imol[best_solvent]/s.F_mol>0.9])
solute_product = TargetProduct('solute_product',
                               criteria = [lambda s: s.imol[solute]/s.F_mol>0.9])

def solvent_recovery_criterion(streams, solvent=best_solvent, extract=MSMS1.extract):
    solvent_prod_streams = [s for s in streams if solvent_product.passes_all_criteria(s)]
    solvent_mol = sum([s.imol[best_solvent] for s in solvent_prod_streams])
    return solvent_mol/extract.imol[solvent] > 0.9

def solute_recovery_criterion(streams, solute=solute, extract=MSMS1.extract):
    solute_prod_streams = [s for s in streams if solute_product.passes_all_criteria(s)]
    solute_mol = sum([s.imol[solute] for s in solute_prod_streams])
    return solute_mol/extract.imol[solute] > 0.9

TPS = TargetProductsSet('TPS', target_products=(solvent_product, solute_product),
                        holistic_criteria=[solvent_recovery_criterion, solute_recovery_criterion])

trains = get_all_possible_distillation_trains(distillation_superstructure=dist_ss,
                                              target_products_set=TPS,
                                              )
