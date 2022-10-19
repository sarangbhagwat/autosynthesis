# -*- coding: utf-8 -*-
"""
Created on Mon Oct  3 11:30:06 2022

@author: sarangbhagwat
"""
import biosteam as bst
from biosteam import SystemFactory

import thermosteam as tmo
import numpy as np

from apd.apd_utils_c import distill_to_azeotropic_composition

flowsheet = bst.Flowsheet('AD_sys')
bst.main_flowsheet.set_flowsheet(flowsheet)

# flowsheet = bst.main_flowsheet()

#%% Streams

tmo.settings.set_thermo(['Water', 'Ethanol', 'AceticAcid', 'Toluene'])

s1 = tmo.Stream('s1')
s1.imol['Ethanol'] = 0.10
s1.imol['Water'] = 0.90

s2 = tmo.Stream('s2')
s2.imol['Ethanol'] = 0.96
s2.imol['Water'] = 0.04

#%% Units
@SystemFactory(ID = 'AD_sys')
def create_AD_sys(ins, outs):
    M1 = bst.Mixer('M1', ins=(s1, ''))
    P1 = bst.Pump('P1', ins=M1-0, P=101325.)
    M1.simulate()
    P1.simulate()
    
    D1 = distill_to_azeotropic_composition(stream=P1-0, LHK=('Ethanol', 'Water'), 
                                          P=101325., x_bot=1e-3, k=1.2, 
                                          vessel_material='Stainless steel 316',
                                          partial_condenser=False,
                                          is_divided=True,
                                          composition_steps=100,
                                          min_y_top=1e-3,
                                          max_y_top=0.999,
                                          column_ID='D1',
                                          azeotrope_error_identifier_substring='cannot meet',
                                          )
    

    P2 = bst.Pump('P2', ins=D1-0, P=20.*101325.) 
    
    D2 = bst.BinaryDistillation('D2', ins=P2-0,
                                        outs=(),
                                        LHK=('Water', 'Ethanol'),
                                        is_divided=True,
                                        
                                        P=20.*101325.,
                                        
                                        product_specification_format='Composition',
                                        y_top=0.999, x_bot=1.-0.995,
                                        
                                        # product_specification_format='Recovery',
                                        # Lr=0.999, Hr=0.999, 
                                        
                                        
                                        k=1.2, 
                                        vessel_material='Stainless steel 316',
                                        partial_condenser=False,
                                        
                                        # condenser_thermo = ideal_thermo,
                                        # boiler_thermo = ideal_thermo,
                                        # thermo=ideal_thermo,
                                        )

    
    D2-1-1-M1
    
    globals().update({u.ID:u for u in flowsheet.unit})



    
#%% Run

AD_sys = create_AD_sys()
AD_sys.simulate()


#%% Unused code

# D1 = bst.BinaryDistillation('D1', ins=P1-0,
#  outs=(),
#                                     LHK=('Ethanol', 'Water'),
#                                     is_divided=True,
                                    
#                                     P=101325.,
                                    
#                                     product_specification_format='Composition',
#                                     y_top=0.82, x_bot=1.-0.999,
                                    
#                                     # product_specification_format='Recovery',
#                                     # Lr=0.99, Hr=0.99, 
                                    
                                    
#                                     k=1.5, 
#                                     vessel_material='Stainless steel 316',
#                                     partial_condenser=False,
                                    
#                                     # condenser_thermo = ideal_thermo,
#                                     # boiler_thermo = ideal_thermo,
#                                     # thermo=ideal_thermo,
#                                     )


# def D2_of(y_top):
#     D2.y_top=y_top
#     try:
#         D2._run()
#         D2._design()
#         return D2.x_bot - 0.005
#     except:
#         return 1

# D2.specification = bst.BoundedNumericalSpecification(D2_of, 1e-5, 1-1e-5)

# @D2.add_specification(run=True):
#     def D2_spec():
#         mol_etoh, mol_water = D2.ins[0].imol['Ethanol'], D2.ins[0].imol['Water']
#         y_top, x_bot = D2.y_top, D2.x_bot


# H2 = bst.HXutility('H2', ins=D2-0, V=0., rigorous=True)


#%% 

# # won't respond to changes in flow:
# self.flocculant_cost = 30 #$/h; Calculated for the baseline 
# # based on a price of $20/kg and a flow of 1.5 kg/h

# # will respond to changes in flow:
# self.flocculant_price = 20 #$/h
# self.flocculant_flow = 1.5 # kg/h

# @property
# def flocculant_cost():
#     return self.flocculant_price*self.flocculant_flow

