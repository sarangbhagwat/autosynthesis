# -*- coding: utf-8 -*-
# APD: The Automated Process Design package.
# Copyright (C) 2020-2023, Sarang Bhagwat <sarangb2@illinois.edu>
# 
# This module is under the UIUC open-source license. See 
# github.com/sarangbhagwat/hxn/blob/master/LICENSE.txt
# for license details.
"""
Created on Sat Apr 2 21:25:33 2022

@author: sarangbhagwat
"""
#%% Imports and setup
import thermosteam as tmo
import biosteam as bst
from thermosteam import Stream
import numpy as np
from math import log as ln
from matplotlib import pyplot as plt

f = bst.main_flowsheet
u = f.unit
np_multiply_elementwise = np.multiply
Stream = tmo.Stream

R = 8.31446261815324 #kJ/kmol/K or J/mol/K
DAC = tmo.equilibrium.activity_coefficients.DortmundActivityCoefficients
# FC = tmo.equilibrium.fugacity_coefficients.FugacityCoefficients
#%% Functions
def get_dGmix_ideal(stream):
    stream_F_mol = stream.F_mol
    vlle_chemicals = [i.ID for i in stream.available_chemicals]
    # stream_F_mol = sum([stream.imol[ID] for ID in vlle_chemicals])
    # print(stream.ID)
    # print([(stream.imol[ID]/stream_F_mol) for ID in vlle_chemicals])
    return stream_F_mol * R * stream.T\
        * sum([
            (stream.imol[ID]/stream_F_mol) * ln(stream.imol[ID]/stream_F_mol)
            for ID in vlle_chemicals if stream.imol[ID]>0.
            ])
    #kJ/h
    
# def get_dGmix_excess(stream, vlle_chemicals):
#     return 0. #TODO
#     #kJ/h

# def get_dGmix(stream, vlle_chemicals):
#     return get_dGmix_ideal(stream, vlle_chemicals) + get_dGmix_excess(stream, vlle_chemicals)
#     #kJ/h

def get_dGmix(stream, aco=None):
    vlle_chemicals = stream.available_chemicals
    stream_F_mol = stream.F_mol
    x = stream.mol[:]/stream.F_mol
    # print(x)
    if not aco:
        aco = DAC(vlle_chemicals)
    ac = aco.activity_coefficients(x, stream.T)
    activities = np_multiply_elementwise(x, ac)
    # print(activities)
    return stream_F_mol * R * stream.T\
        * sum([
            # (stream.imol[ID]/stream_F_mol) * ln(stream.imol[ID]/stream_F_mol)
            # for ID in vlle_chemicals if stream.imol[ID]>0.
            ai * ln(ai) for ai in activities
            ])
    
def get_dGsep(feed_streams_set, product_streams_set):
    dG_mix_feed = sum([get_dGmix(fs) for fs in feed_streams_set])
    dG_mix_product = sum([get_dGmix(ps) for ps in product_streams_set])
    
    return dG_mix_product - dG_mix_feed
    #kJ/h

def get_E_volatility_sep(feed_streams_set, product_streams_set,
                         heat_transfer_efficiency=0.8):
    feed_stream = feed_streams_set[0]
    top_stream = product_streams_set[0]
    bottom_stream = product_streams_set[1]
    gibbs_free_energy_separation = get_dGsep(feed_streams_set, product_streams_set)
    min_sensible_heat = sum([i.Cp(T=top_stream.T, phase='l')*top_stream.imol[i.ID]*(top_stream.T-feed_stream.T)
        for i in top_stream.vle_chemicals])
    min_latent_heat = sum([i.Hvap(top_stream.T)*top_stream.imol[i.ID] 
         for i in top_stream.vle_chemicals])
    return (gibbs_free_energy_separation + min_sensible_heat + min_latent_heat)/heat_transfer_efficiency
        

get_heating_demand = lambda unit: sum([i.duty for i in unit.heat_utilities if i.duty*i.flow>0])

def get_E_volatility_separation(feed_streams_set, product_streams_set,
                         heat_transfer_efficiency=0.8):
    vle_chemicals_sorted = []
    for fs in feed_streams_set:
        vle_chemicals_sorted.append(get_vle_components_sorted(fs))
    
#%% Examples
tmo.settings.set_thermo(['Water', 'AceticAcid', 'Ethanol'])
# tmo.settings.set_thermo(['Water', 'Ethanol'])
stream = tmo.Stream('stream')
stream.imass['Ethanol'] = 11.1
stream.imass['Water'] = 100-11.1
stream.imass['AceticAcid'] = 1
# F401 = bst.Flash('F401', ins=stream, outs = ('volatiles', 'bottom_product_esters'), 
#                  V = 0.05, 
#                  P=101325.)
# F401.simulate()

# print(get_dGsep([stream], F401.outs))


feed_streams_set=[stream]
product_streams_set=[tmo.Stream('p1', Ethanol=0.99*stream.imol['Ethanol'], Water=0.01*stream.imol['Water'],
                                AceticAcid=0.01*stream.imol['AceticAcid'],
                                ), 
                     tmo.Stream('p2', Ethanol=0.01*stream.imol['Ethanol'], Water=0.99*stream.imol['Water'],
                                AceticAcid=0.99*stream.imol['AceticAcid'],
                                )]
water_splits = np.linspace(1e-5, 1-1e-5, 100)
dGseps = []
for ws in water_splits:
    product_streams_set[0].imol['Water'] = ws*stream.imol['water']
    product_streams_set[1].imol['Water'] = (1-ws)*stream.imol['water']
    dGseps.append(get_dGsep(feed_streams_set, product_streams_set,))
plt.plot(water_splits, dGseps)

# D401 = bst.units.BinaryDistillation('D401', ins=stream.copy(), outs=('D401_g', 'D401_l'),
#                                     LHK=('Ethanol', 'Water'),
#                                     is_divided=True,
#                                     product_specification_format='Recovery',
#                                     Lr=0.9, Hr=0.9, k=1.05, P = 101325./20.,
#                                     vessel_material = 'Stainless steel 316',
#                                     partial_condenser = False,
#                                     # condenser_thermo = ideal_thermo,
#                                     # boiler_thermo = ideal_thermo,
#                                     # thermo=ideal_thermo,
#                                     )

#%% Node examples
feed_stream = Stream('feed_stream', Ethanol=10., Water=10., AceticAcid=1.)
feed_streams = [feed_stream]
goal_ethanol = Stream('goal_ethanol', Ethanol=10.-1e-2, Water=1e-2, AceticAcid=1e-3)
goal_liquid_wastes = Stream('goal_liquid_wastes', Ethanol=1e-2, Water=10.-1e-2, AceticAcid=1.-1e-3)
goal_product_streams = [goal_ethanol, goal_liquid_wastes]

h_cost = lambda current_set, goal_set: get_E_volatility_sep(current_set, goal_set)
f_cost = lambda units: sum([get_heating_demand(unit) for unit in units if unit.ins[0]])
g_cost = lambda units, current_set, goal_set: f_cost(units) + h_cost(current_set, goal_set) 

# d1 = add_distillation_column(feed_stream, LHK=('Ethanol', 'Water'),
#                              Lr=0.999, Hr=0.999,
#                              column_type='ShortcutColumn')

#%% State representation utils

class Node:
    def __init__(self, parent, units, goal_product_streams):
        self.sys = sys = sys_from_units(f'sys_{int(10000*np.random.random())}', units)
        self.streams = streams = list(sys.streams)
        self._units = units
        self.parent = parent
        self.goal_product_streams = goal_product_streams
        # self.units = sys.units
        try:
            self.sys.simulate()
        except Exception as e:
            del(self)
            raise RuntimeError(f'Infeasible node:\n{e}')
        
        self._g_cost = g_cost(units, streams, goal_product_streams)
        
        
    @property
    def g_cost(self):
        if self._g_cost:
            return self._g_cost
        return g_cost(self.units, self.streams, self.goal_product_streams)
    
    @property
    def ID(self):
        return self.sys.ID
    
    @property
    def units(self):
        if self._units:
            return self._units
        return self.sys.units
    
    @units.setter
    def units(self, new_units):
        self.sys = new_sys = sys_from_units(f'sys_{int(10000*np.random.random())}', new_units)
        self.streams = list(new_sys.streams)
        self.units = new_units
    
    # @property
    # def sys(self):
    #     return self.sys
    
#%% State transition utilities

BinaryDistillation = bst.units.BinaryDistillation
ShortcutColumn = bst.units.ShortcutColumn
Flash = bst.Flash
sys_from_units = bst.System.from_units

def add_distillation_column(in_stream,
                            LHK, 
                            Lr, Hr,
                            column_type='BinaryDistillation',
                            ID=None,
                            k=1.05, P=101325., 
                            is_divided=True,
                            partial_condenser=False,
                            vessel_material='Stainless steel 316',
                            ):
    if not ID:
        ID=f'{stream.ID}_{column_type}'
    new_column = None
    if column_type =='BinaryDistillation':
        new_column = BinaryDistillation(ID, ins=in_stream, outs=(f'{ID}_0', f'{ID}_1'),
                                            LHK=LHK,
                                            is_divided=is_divided,
                                            product_specification_format='Recovery',
                                            Lr=Lr, Hr=Hr, k=k, P=P,
                                            vessel_material=vessel_material,
                                            partial_condenser=partial_condenser,
                                            # condenser_thermo = ideal_thermo,
                                            # boiler_thermo = ideal_thermo,
                                            # thermo=ideal_thermo,
                                            )
    elif column_type =='ShortcutColumn':
        new_column = ShortcutColumn(ID, ins=in_stream, outs=(f'{ID}_0', f'{ID}_1'),
                                            LHK=LHK,
                                            is_divided=is_divided,
                                            product_specification_format='Recovery',
                                            Lr=Lr, Hr=Hr, k=k, P=P,
                                            vessel_material=vessel_material,
                                            partial_condenser=partial_condenser,
                                            # condenser_thermo = ideal_thermo,
                                            # boiler_thermo = ideal_thermo,
                                            # thermo=ideal_thermo,
                                            )
    return new_column

def add_flash_vessel(in_stream,
                    V, 
                    ID=None,
                    P=101325., 
                    vessel_material='Stainless steel 316',
                    ):
    if not ID:
        ID=f'{stream.ID}_Flash'
    return Flash(ID, ins=in_stream, outs=(f'{ID}_0', f'{ID}_1'), 
                     V=V, 
                     P=P)


def add_node(parent_node, stream, unit_to_add, **kwargs):
    if unit_to_add == 'ShortcutColumn':
        LHK, Lr, Hr = kwargs.values()
        new_unit = add_distillation_column(stream, LHK=LHK,
                                Lr=Lr, Hr=Lr,
                                column_type='ShortcutColumn')
    elif unit_to_add == 'Flash':
        V, P = kwargs.values()
        new_unit = add_flash_vessel(stream, V=V,
                                P=P,)
        # new_unit.simulate()
    return Node(parent_node, list(parent_node.units)+[new_unit], parent_node.goal_product_streams)
    
def get_vle_components_sorted(stream, cutoff_mol=1e-3):
    # vle_chemicals = stream.vle_chemicals
    sorted_list = list([i for i in stream.vle_chemicals if stream.imol[i.ID]>cutoff_mol])
    sorted_list.sort(key=lambda i: i.Tb)
    return sorted_list

def get_candidate_LHK_pairs(stream, cutoff_mol=1e-3):
    sorted_list = get_vle_components_sorted(stream=stream, cutoff_mol=cutoff_mol)
    sorted_list_strings = [i.ID for i in sorted_list]
    return [(sorted_list_strings[i], sorted_list_strings[i+1]) 
            for i in range(len(sorted_list_strings)-1)]