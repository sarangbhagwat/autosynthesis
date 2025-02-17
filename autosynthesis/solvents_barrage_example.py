"""
Created on Thu Apr  7 12:40:12 2022

@author: sarangbhagwat
"""

#%% Imports

from autosynthesis.solvents_barrage import run_solvents_barrage, get_candidate_solvents_ranked
import biosteam as bst
import thermosteam as tmo

#%% Initialize chemicals (no need to initialize solvent chemicals) and feed streams. 
#   This can be done in an external module (e.g., your biorefinery) and you can simply import your feed stream.

tmo.settings.set_thermo(['Water', '2,3-Butanediol', 'AceticAcid', 'Glycerol', '1-Dodecanol'])
stream = tmo.Stream('stream')
stream.imass['Water'] = 1000.
stream.imass['2,3-Butanediol'] = 80.
stream.imass['AceticAcid'] = 20.
stream.imass['Glycerol'] = 20.

# from biorefineries import lactic
# lactic.load()
# stream = lactic.flowsheet.S402.outs[1]

#%% Run

results = get_candidate_solvents_ranked(stream=stream, # Stream from which you wish to extract the solute
                     solute_ID='2,3-Butanediol', # solute chemical ID
                     impurity_IDs=[i.ID for i in stream.lle_chemicals if not i.ID in ('Water', '2,3-Butanediol')], # List of IDs of impurities in "stream" that you want get partitioning results for, other than water; note that all chemicals in the stream will affect LLE interaction effects, regardless of which chemicals are present in impurity_IDs
                     T=70.+273.15, # Temperature (K) at which you wish to run the solvents barrage; temperature (K) of "stream" by default
                     stream_modifiers='baseline_stream', # String: 'baseline_stream' to analyze the "stream" passed in arguments; 'impurity_free_stream' to remove the impurities listed in impurity_IDs before performing analyses; 'solute_in_pure_water' to analyze simply for the solute in pure water
                      solvent_IDs = [ # Use CAS numbers if common/iupac names are not recognized by the Chemicals package
                                      'Pentadecanol',
                                      'Tridecanol',
                                      'Ethanol',
                                      'Methanol',
                                      'Propyl acetate',
                                      'Butyl acetate',
                                      'Hexanol',
                                      'Hexane',
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
                                      'Diethyl sebacate', # No Psat, Hvap
                                      # 'Glycerol',
                                      'Toluene',
                                      'Trioctylamine',
                                      'Isoamyl alcohol',
                                      # '5137-55-3', # CAS number for Aliquat 336
                                      # 'Water',
                                      'Benzene',
                                      '143-28-2', # CAS number for Oleyl alcohol
                                      'Tetrahydrofuran'
                                      ],
                     plot_Ks=True,
                     save_excel=False,
                     save_K_plots=True,
                     )

#%% Try in a solvent extraction unit

solvent_stream = tmo.Stream('solvent_stream')
solvent_stream.imol['1-Dodecanol'] = 4*stream.imol['Water']

M1 = bst.Mixer('M1', ins=(stream, solvent_stream), outs=('mixed_stream'))

MSMS = bst.MultiStageMixerSettlers(ID='MSMS', 
                                   ins=M1-0, 
                                   thermo=M1.outs[0].thermo, 
                                   outs=('MSMS_extract', 'MSMS_raffinate'), 
                                   N_stages=5, 
                                   solvent_ID='1-Dodecanol',
                                   # partition_data = partition_data,
                                   )

M1.simulate()
MSMS.simulate()
