"""
Created on Thu Apr  7 12:40:12 2022

@author: sarangbhagwat
"""

#%% Imports

from apd.solvents_barrage import run_solvents_barrage
import thermosteam as tmo

#%% Initialize chemicals (no need to initialize solvent chemicals) and feed streams. 
#   This can be done in an external module (e.g., your biorefinery) and you can simply import your feed stream.

tmo.settings.set_thermo(['Water', '2,3-Butanediol', 'AceticAcid', 'Glycerol'])
stream = tmo.Stream('stream')
stream.imass['Water'] = 1000.
stream.imass['2,3-Butanediol'] = 50.
stream.imass['AceticAcid'] = 20.
stream.imass['Glycerol'] = 20.

#%% Run

results = run_solvents_barrage(stream=stream, # Stream from which you wish to extract the solute
                     solute_ID='2,3-Butanediol', # solute chemical ID
                     impurity_IDs=['AceticAcid', 'Glycerol'], # List of IDs of impurities in "stream" that you want get partitioning results for, other than water; note that all chemicals in the stream will affect LLE interaction effects, regardless of which chemicals are present in impurity_IDs
                     T=30.+273.15, # Temperature (K) at which you wish to run the solvents barrage; temperature (K) of "stream" by default
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
                                     ]
                     )

