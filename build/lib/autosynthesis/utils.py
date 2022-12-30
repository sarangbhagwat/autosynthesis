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
from .units import APDBatchCrystallizer
from .solvents_barrage import get_candidate_solvents_ranked, solvent_IDs
from thermosteam import Chemical, Stream
from copy import deepcopy 
from warnings import filterwarnings
from networkx.classes.function import path_weight        
import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations

__all__ = ('get_separation_units')
#%%
# from apd.apd_utils_c import mock_pressure_swing_distillation, distill_to_azeotropic_composition
filterwarnings("ignore")

f = bst.main_flowsheet
u = f.unit
np_multiply_elementwise = np.multiply

R = 8.31446261815324 #kJ/kmol/K or J/mol/K
DAC = tmo.equilibrium.activity_coefficients.DortmundActivityCoefficients
# FC = tmo.equilibrium.fugacity_coefficients.FugacityCoefficients

SolidsCentrifuge = bst.SolidsCentrifuge


#%%
def distill_to_azeotropic_composition(stream, LHK, 
                                      P=101325., x_bot=1e-3, k=1.2, 
                                      vessel_material='Stainless steel 316',
                                      partial_condenser=False,
                                      is_divided=True,
                                      composition_steps=100,
                                      min_y_top=1e-3,
                                      max_y_top=0.999,
                                      column_ID='',
                                      azeotrope_error_identifier_substring='cannot meet',
                                      ):
    temp_column = bst.BinaryDistillation(column_ID, 
                                        ins=stream,
                                        outs=(),
                                        LHK=LHK,
                                        is_divided=is_divided,
                                        
                                        P=P,
                                        
                                        product_specification_format='Composition',
                                        y_top=0.5, x_bot=x_bot,

                                        k=k, 
                                        vessel_material=vessel_material,
                                        partial_condenser=partial_condenser,
                                        )
    
    y_tops = np.linspace(min_y_top, max_y_top, composition_steps)
    curr_y_top_index = 0
    for yti in range(len(y_tops)):
        curr_y_top_index = yti
        try:
            temp_column.y_top = y_tops[curr_y_top_index]
            # temp_column.show('cmol100')
            temp_column._run()
            temp_column._design()
            # temp_column.show('cmol100')
        except RuntimeError as e:
            if azeotrope_error_identifier_substring in str(e):
                break
            elif 'molar fraction of the light key in the feed must be between the bottoms product and distillate compositions'\
                in str(e): # maximum boiling azeotrope
                # raise e
                # print(y_tops[curr_y_top_index], str(e))
                pass
            else:
                pass
        except:
            pass
        
    temp_column.y_top = y_tops[curr_y_top_index-1]
    # temp_column.show('cmol100')
    # print(temp_column.y_top, LHK)
    temp_column.simulate()
    
    return temp_column

def get_max_P_for_evap(chem_ID,
                       max_T=None):
    if not max_T:
        max_T = bst.HeatUtility.heating_agents[2].T-4.5
        
    tempstream = tmo.Stream('tempstream')
    tempstream.imol[chem_ID] = 1.
    return tempstream.bubble_point_at_T(max_T).P
    
def mock_pressure_swing_distillation(stream, LHK, 
                                      Ps=(101325., 20*101325.), x_bot=1e-3, k=1.2, 
                                      vessel_material='Stainless steel 316',
                                      partial_condenser=False,
                                      is_divided=True,
                                      composition_steps=100,
                                      min_y_top=1e-3,
                                      max_y_top=0.999,
                                      # column_IDs=('temp_column_1', 'temp_column_2'),
                                      azeotrope_error_identifier_substring='cannot meet',
                                      target_column2_LK_recovery = 0.999,
                                      target_column2_ytop = 0.995,
                                      ):
    chems = stream.chemicals
    stream_LHK_only = stream.copy()
    stream_LK_only = tmo.Stream()
    stream_LK_only.imol[LHK[0]]
    stream_HK_only = tmo.Stream()
    stream_ID = stream.ID
    column_IDs = (f'{stream_ID}_psd_column_1', f'{stream_ID}_psd_column_2')
    # stream_LHK_only.P = Ps[0]
    for i in chems:
        if not i.ID in LHK:
            stream_LHK_only.imol[i.ID] = 0.
    T_bubble = stream_LHK_only.bubble_point_at_P(Ps[0]).T
    if T_bubble > chems[LHK[1]].Tb and T_bubble > chems[LHK[0]].Tb :
        stream.show('cmol100')
        raise RuntimeError(f'{LHK} forms a maximum-boiling azeotrope; {T_bubble} > {chems[LHK[0]].Tb} and {T_bubble} > {chems[LHK[1]].Tb}.)')
    
    
    temp_pump_1 = bst.Pump(f'{stream_ID}_psd_pump_1', ins=stream, P=Ps[0])
    temp_pump_1.simulate()
    
    temp_column_1 = distill_to_azeotropic_composition(stream=temp_pump_1-0, LHK=LHK,
                                                      P=Ps[0], x_bot=x_bot, k=k,
                                                      vessel_material=vessel_material,
                                                      partial_condenser=partial_condenser,
                                                      is_divided=is_divided,
                                                      composition_steps=composition_steps,
                                                      min_y_top=min_y_top,
                                                      max_y_top=max_y_top,
                                                      column_ID=column_IDs[0],
                                                      azeotrope_error_identifier_substring=azeotrope_error_identifier_substring,)
    
    temp_pump_2 = bst.Pump(f'{stream_ID}_psd_pump_2', ins=temp_column_1-0, P=Ps[1])
    
    
    temp_pump_2.simulate()
    temp_column_2 = None
    try:
        temp_column_2 = bst.ShortcutColumn(column_IDs[1], 
                                            ins=temp_pump_2-0,
                                            outs=(),
                                            LHK=[LHK[1], LHK[0]],
                                            is_divided=is_divided,
                                            
                                            P=Ps[1],
                                            
                                            product_specification_format='Composition',
                                            y_top=target_column2_ytop, x_bot=x_bot,
    
                                            k=k, 
                                            vessel_material=vessel_material,
                                            partial_condenser=partial_condenser,
                                            )
        @temp_column_2.add_specification(run=True)
        def temp_column_2_spec():
            temp_column_2.y_top = target_column2_ytop
            instream = temp_column_2.ins[0]
            total_flow = instream.F_mol
            total_LK_flow = instream.imol[temp_column_2.LHK[0]]
            
            LK_top_flow = total_LK_flow*target_column2_LK_recovery
            total_top_flow = LK_top_flow*(1-target_column2_ytop)/target_column2_ytop
            
            total_bottom_flow = total_flow - total_top_flow
            # HK_bottom_flow = instream.imol[LHK[1]] - (total_top_flow-LK_top_flow)
            LK_bottom_flow = total_LK_flow - LK_top_flow
            temp_column_2.x_bot = LK_bottom_flow/total_bottom_flow
        temp_column_2.simulate()
        
        
    except:
        try:
            temp_column_2 = bst.ShortcutColumn(column_IDs[1], 
                                                ins=temp_pump_2-0,
                                                outs=(),
                                                LHK=LHK,
                                                is_divided=is_divided,
                                                
                                                P=Ps[1],
                                                
                                                product_specification_format='Composition',
                                                y_top=target_column2_ytop, x_bot=x_bot,
        
                                                k=k, 
                                                vessel_material=vessel_material,
                                                partial_condenser=partial_condenser,
                                                )
            @temp_column_2.add_specification(run=True)
            def temp_column_2_spec():
                temp_column_2.y_top = target_column2_ytop
                instream = temp_column_2.ins[0]
                total_flow = instream.F_mol
                total_LK_flow = instream.imol[temp_column_2.LHK[0]]
                
                LK_top_flow = total_LK_flow*target_column2_LK_recovery
                total_top_flow = LK_top_flow*(1-target_column2_ytop)/target_column2_ytop
                
                total_bottom_flow = total_flow - total_top_flow
                # HK_bottom_flow = instream.imol[LHK[1]] - (total_top_flow-LK_top_flow)
                LK_bottom_flow = total_LK_flow - LK_top_flow
                temp_column_2.x_bot = LK_bottom_flow/total_bottom_flow
            temp_column_2.simulate()
        
        except:
            try:
                temp_column_2 = bst.ShortcutColumn(column_IDs[1], 
                                                    ins=temp_pump_2-0,
                                                    outs=(),
                                                    LHK=[LHK[1], LHK[0]],
                                                    is_divided=is_divided,
                                                    
                                                    P=Ps[1],
                                                    
                                                    # product_specification_format='Composition',
                                                    # y_top=target_column2_ytop, x_bot=x_bot,
            
                                                    product_specification_format='Recovery',
                                                    Lr=0.999, Hr=0.999,
                                                    k=k, 
                                                    vessel_material=vessel_material,
                                                    partial_condenser=partial_condenser,
                                                    )
                temp_column_2.simulate()
            
            except:
                temp_column_2 = bst.ShortcutColumn(column_IDs[1], 
                                                    ins=temp_pump_2-0,
                                                    outs=(),
                                                    LHK=LHK,
                                                    is_divided=is_divided,
                                                    
                                                    P=Ps[1],
                                                    
                                                    # product_specification_format='Composition',
                                                    # y_top=target_column2_ytop, x_bot=x_bot,
            
                                                    product_specification_format='Recovery',
                                                    Lr=0.999, Hr=0.999,
                                                    k=k, 
                                                    vessel_material=vessel_material,
                                                    partial_condenser=partial_condenser,
                                                    )
                temp_column_2.simulate()
    
    temp_LK_mixer = bst.Mixer(f'{stream_ID}_LK_mixer', ins=(temp_column_2-0))
    temp_LK_mixer.simulate()
    
    temp_HK_mixer = bst.Mixer(f'{stream_ID}_HK_mixer', ins=(temp_column_1-1, temp_column_2-1))
    temp_HK_mixer.simulate()
    
    return (temp_pump_1, temp_column_1, temp_pump_2, temp_column_2, temp_LK_mixer, temp_HK_mixer)

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
# tmo.settings.set_thermo(['Water', 'AceticAcid', 'Ethanol'])
# # tmo.settings.set_thermo(['Water', 'Ethanol'])
# stream = tmo.Stream('stream')
# stream.imass['Ethanol'] = 11.1
# stream.imass['Water'] = 100-11.1
# stream.imass['AceticAcid'] = 1
# # F401 = bst.Flash('F401', ins=stream, outs = ('volatiles', 'bottom_product_esters'), 
# #                  V = 0.05, 
# #                  P=101325.)
# # F401.simulate()

# # print(get_dGsep([stream], F401.outs))


# feed_streams_set=[stream]
# product_streams_set=[tmo.Stream('p1', Ethanol=0.99*stream.imol['Ethanol'], Water=0.01*stream.imol['Water'],
#                                 AceticAcid=0.01*stream.imol['AceticAcid'],
#                                 ), 
#                      tmo.Stream('p2', Ethanol=0.01*stream.imol['Ethanol'], Water=0.99*stream.imol['Water'],
#                                 AceticAcid=0.99*stream.imol['AceticAcid'],
#                                 )]
# water_splits = np.linspace(1e-5, 1-1e-5, 100)
# dGseps = []
# for ws in water_splits:
#     product_streams_set[0].imol['Water'] = ws*stream.imol['water']
#     product_streams_set[1].imol['Water'] = (1-ws)*stream.imol['water']
#     dGseps.append(get_dGsep(feed_streams_set, product_streams_set,))
# plt.plot(water_splits, dGseps)

# # D401 = bst.units.BinaryDistillation('D401', ins=stream.copy(), outs=('D401_g', 'D401_l'),
# #                                     LHK=('Ethanol', 'Water'),
# #                                     is_divided=True,
# #                                     product_specification_format='Recovery',
# #                                     Lr=0.9, Hr=0.9, k=1.05, P = 101325./20.,
# #                                     vessel_material = 'Stainless steel 316',
# #                                     partial_condenser = False,
# #                                     # condenser_thermo = ideal_thermo,
# #                                     # boiler_thermo = ideal_thermo,
# #                                     # thermo=ideal_thermo,
# #                                     )

#%% Node examples
# feed_stream = Stream('feed_stream', Ethanol=10., Water=10., AceticAcid=1.)
# feed_streams = [feed_stream]
# goal_ethanol = Stream('goal_ethanol', Ethanol=10.-1e-2, Water=1e-2, AceticAcid=1e-3)
# goal_liquid_wastes = Stream('goal_liquid_wastes', Ethanol=1e-2, Water=10.-1e-2, AceticAcid=1.-1e-3)
# goal_product_streams = [goal_ethanol, goal_liquid_wastes]

#%% Node cost functions
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
            self._g_cost = g_cost(units, streams, goal_product_streams)
        except Exception as e:
            del(self)
            raise RuntimeError(f'Infeasible node:\n{e}')
        
        
        
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
        ID=f'{in_stream.ID}_{column_type}'
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
                    thermo=None
                    ):
    if not thermo:
        thermo=in_stream.thermo
    if not ID:
        ID=f'{in_stream.ID}_Flash'
    return Flash(ID, ins=in_stream, outs=(f'{ID}_0', f'{ID}_1'), 
                     V=V, 
                     P=P,
                     thermo=thermo)


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

# def distill_to_azeotropic_composition(stream, LHK, 
#                                       P=101325., x_bot=1e-3, k=1.2, 
#                                       vessel_material='Stainless steel 316',
#                                       partial_condenser=False,
#                                       is_divided=True,
#                                       composition_steps=100,
#                                       min_y_top=1e-3,
#                                       max_y_top=0.999,
#                                       column_ID='',
#                                       azeotrope_error_identifier_substring='cannot meet',
#                                       ):
#     temp_column = bst.BinaryDistillation(column_ID, 
#                                         ins=stream,
#                                         outs=(),
#                                         LHK=LHK,
#                                         is_divided=is_divided,
                                        
#                                         P=P,
                                        
#                                         product_specification_format='Composition',
#                                         y_top=0.5, x_bot=x_bot,

#                                         k=k, 
#                                         vessel_material=vessel_material,
#                                         partial_condenser=partial_condenser,
#                                         )
    
#     y_tops = np.linspace(min_y_top, max_y_top, composition_steps)
#     curr_y_top_index = 0
#     for yti in range(len(y_tops)):
#         curr_y_top_index = yti
#         try:
#             temp_column.y_top = y_tops[curr_y_top_index]
#             temp_column._run()
#             temp_column._design()
#         except RuntimeError as e:
#             if azeotrope_error_identifier_substring in str(e):
#                 break
#             else:
#                 # raise e
#                 pass
#         except:
#             pass
        
#     temp_column.y_top = y_tops[curr_y_top_index-1]
#     temp_column.simulate()
    
#     return temp_column

#%% DAG-TS utils
class APDStream:
    def __init__(self,composition_dict,
                 products,
                 impurities,
                 ID=None):
        chems = []
        if not ID:
            ID = f's_{int(1e6*round(np.random.rand(), 6))}'
        for k in composition_dict.keys():
            if type(k)==str:
                chems.append(Chemical(k))
            else:
                chems.append(k)
        tmo.settings.set_thermo(chems)
        self.ID = ID
        self.stream = stream = Stream(ID=ID)
        for k, v in composition_dict.items():
            if type(k)==str:
                stream.imol[k] = v
            else:
                stream.imol[k.ID] = v
        
        self.products = products
        self.impurities = impurities
    
    def __repr__(self):
        self.stream.show('cmol100')
        return f''
    

class SequentialDistillationResult:
    def __init__(self, result):
        self.stream = result[0][0]
        self.products = result[0][1]
        self.impurities = result[0][2]
        self.score = result[1]
        self.columns = result[2]
        self.azeotropes = result[3]
        self.exceptions = []
        
    def __repr__(self):
        return f'\nSequentialDistillationResult\nStream: {self.stream.ID}\nProducts: {self.products}\nImpurities: {self.impurities}\nAzeotropic key pairs ({len(self.azeotropes)} total): {self.azeotropes}\nExceptions: {self.exceptions}\nScore: {self.score}\n'

get_heating_demand = lambda unit: sum([i.duty for i in unit.heat_utilities if i.duty*i.flow>0])

def get_vle_components_sorted(stream, cutoff_Z_mol=1e-3):
    # vle_chemicals = stream.vle_chemicals
    sorted_list = list([i for i in stream.vle_chemicals if stream.imol[i.ID]/stream.F_mol>cutoff_Z_mol])
    sorted_list.sort(key=lambda i: i.Tb if i.Tb else np.inf)
    return sorted_list

def add_flash_vessel(in_stream,
                    V, 
                    ID=None,
                    P=101325., 
                    vessel_material='Stainless steel 316',
                    ):
    if not ID:
        ID=f'{in_stream.ID}_Flash'
    return Flash(ID, ins=in_stream, outs=(f'{ID}_0', f'{ID}_1'), 
                     V=V, 
                     P=P)

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
        ID=f'{in_stream.ID}_{column_type}'
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

def add_crystallizer_filter_dryer(in_stream, solute, target_recovery=0.99, tau=6, N=4, 
                        IDs=[None, None, None], get_solubility_vs_T=None,
                        natural_gas_price=0.218):
    if not IDs[0]:
        IDs[0]=f'{in_stream.ID}_crystallizer'
    
    new_crystallizer = APDBatchCrystallizer(IDs[0], ins=in_stream, outs=f'{IDs[0]}_0', 
                                            tau=tau, 
                                            target_recovery=target_recovery, 
                                            solute=solute, 
                                            N=N)
    new_crystallizer.simulate()
    
    if not IDs[1]:
        IDs[1]=f'{in_stream.ID}_filter'
    
    new_filter_recovery = 0.95
    
    new_filter = SolidsCentrifuge(IDs[1], ins=new_crystallizer.outs[0], 
                            outs=(f'{IDs[1]}_{solute}_solid', f'{IDs[1]}_filtrate'),
                            solids=['Yeast', solute], split={'Yeast':1-1e-4, solute:1-1e-4})
    
    @new_filter.add_specification(run=False)
    def new_filter_spec():
        new_filter_solids = new_filter.outs[0]
        new_filter.isplit[solute] = new_filter_recovery*new_filter.ins[0].imol['s', solute]/new_filter.ins[0].imol[solute]
        new_filter._run()
        new_filter_solids.phases = ('s', 'l')
        for c in new_filter_solids.chemicals:
            c_ID = c.ID
            if not (c_ID=='Water' or c_ID =='H2O'):
                new_filter_solids.imol['s',c_ID] = new_filter_solids.imol[c_ID]
                new_filter_solids.imol['l',c_ID] = 0
        new_filter.outs[1].phases = ('l')
        
    new_filter.simulate()
    
    if not IDs[2]:
        IDs[2]=f'{in_stream.ID}_dryer'
    
    natural_gas_drying = Stream(f'natural_gas_drying_{IDs[2]}', units = 'kg/hr', price=0.218)
    
    new_dryer = bst.DrumDryer(IDs[2], ins=(new_filter-0, 'dryer_air_in', natural_gas_drying,),
                         outs=('dry_solids', 'hot_air', 'emissions'),
                         split={solute: 1e-4,
                                    'Yeast': 0.}
                         )
    try:
        new_dryer.simulate()
    except:
        breakpoint()
    # new_dryer.show()
    # new_crystallizer.show()
    # new_filter.show()
    # new_dryer.show()
    
    return [new_crystallizer, new_filter, new_dryer]

def get_sinkless_streams(units, p_chem_IDs):
    ss = []
    for u in units:
        for s in u.outs:
            if not s.sink:
                # print(1)
                if not is_a_product_stream(s, p_chem_IDs)\
                    and not is_a_productless_stream(s, p_chem_IDs):
                        # print(11)
                    ss.append(s)
    return ss

def is_a_product_stream(stream, p_chem_IDs, min_purity=0.8):
    return np.any(np.array([stream.imol[c]/stream.F_mol >= min_purity for c in p_chem_IDs]))
        
def is_a_productless_stream(stream, p_chem_IDs, cutoff_Z_mol=0.2):
    return not np.any(np.array([stream.imol[c]/stream.F_mol >= cutoff_Z_mol for c in p_chem_IDs]))
          
def run_sequential_distillation(stream, products, impurities, 
                                      cutoff_Z_mol=1e-3,
                                score_offset_per_azeotrope=1e9):
    # chemicals = get_thermo().chemicals
    chemicals = stream.chemicals
    tmo.settings.set_thermo(chemicals)
    p_chems = [chemicals[p] for p in products if type(p)==str]
    p_chem_IDs = [pc.ID for pc in p_chems]
    i_chems = [chemicals[i] for i in impurities if type(i)==str]
    i_chem_IDs = [ic.ID for ic in i_chems]
    sorted_chems = get_vle_components_sorted(stream, 1e-3)
    columns = []
    transient_sinkless_streams = [stream]
    azeotropes = []
    try:
        while transient_sinkless_streams:
            # print(transient_sinkless_streams)
            for s in transient_sinkless_streams:
                sorted_chems = get_vle_components_sorted(s, 1e-3)
                LHK=tuple([i.ID for i in sorted_chems[:2]])
                # print(LHK)
                # s.show()
                try:
                    try:
                        new_col = add_distillation_column(in_stream=s,
                                                          LHK=LHK,
                                                          Lr=0.99999, Hr=0.99999,
                                                          P=101325./100,
                                                          column_type ='BinaryDistillation'
                                                          )
                        new_col.simulate()
                        columns.append(new_col)
                    except:
                        try:
                            new_col = add_distillation_column(in_stream=s,
                                                              LHK=LHK,
                                                              Lr=0.99999, Hr=0.99999,
                                                              P=101325./10,
                                                              column_type ='BinaryDistillation'
                                                              )
                            new_col.simulate()
                            columns.append(new_col)
                        except Exception as e:
                            if 'heating agent' in str(e):
                                new_col = add_flash_vessel(in_stream=s,
                                                           V=s.imol[LHK[0]]/sum([s.imol[s_chem.ID] for s_chem in s.vle_chemicals]),
                                                           P=101325./10,
                                                           )
                                new_col.simulate()
                                columns.append(new_col)
                            else:
                                raise e
                except:
                    try:
                        new_col = add_distillation_column(in_stream=s,
                                                          LHK=LHK,
                                                          Lr=0.99999, Hr=0.99999,
                                                          P=101325./100,
                                                          column_type ='ShortcutColumn'
                                                          )
                        new_col.simulate()
                        columns.append(new_col)
                        azeotropes.append(LHK)
                    except:
                        new_col = add_distillation_column(in_stream=s,
                                                          LHK=LHK,
                                                          Lr=0.99999, Hr=0.99999,
                                                          P=101325./10,
                                                          column_type ='ShortcutColumn'
                                                          )
                        new_col.simulate()
                        columns.append(new_col)
                        azeotropes.append(LHK)
            transient_sinkless_streams.clear()
            transient_sinkless_streams += get_sinkless_streams(columns, p_chem_IDs)
            # print(transient_sinkless_streams)
        
        score = sum(get_heating_demand(col) for col in columns)/sum([stream.imol[pci] for pci in p_chem_IDs])
        score += score_offset_per_azeotrope*len(azeotropes)
        return SequentialDistillationResult(result=((stream, p_chem_IDs, i_chem_IDs), score, columns, azeotropes))
    except Exception as e:
        result = SequentialDistillationResult(result=((stream, p_chem_IDs, i_chem_IDs), np.inf, [bst.Unit('EmptyUnit')], []))
        result.exceptions.append(e)
        return result




    
class DAGNode():
    def __init__(self, split_performed, 
                 input_streams,
                 output_streams,
                 # products,
                 ):
        self.split_performed = split_performed
        self.input_streams = set(input_streams)
        self.output_streams = set(output_streams)
        self.ID = split_performed + "//" + str(input_streams) + "-->" + str(output_streams)  
        self.LHK_pointers = None
        # self.products = products
        if self.split_performed:
            split_index = split_performed.index("|")
            self.LHK_pointers = split_performed[split_index-1:split_index], split_performed[split_index+1:split_index+2]
            

def has_edge(ni, nj):
    # nki, nkj = ni.split_performed, nj.split_performed
    # nki_output_streams = ni.output_streams
    # # print(nki, nkj)
    # # print(nj.ID)
    # if nkj=="":
    #     return False
    # split_index = nkj.index('|')
    # # compo_IDs_nki = nki[:split_indices[0]], nki[split_indices[0]+1:]
    # compo_IDs_nkj = nkj[:split_index], nkj[split_index+1:]
    # # fused_compo_IDs_nkj = compo_IDs_nkj[0] + compo_IDs_nkj[1]
    # count=0
    # for nki_os in nki_output_streams:
    #     for cnkj in compo_IDs_nkj:
    #         if cnkj == nki_os:
    #             count+=1
    # if count==2:
    #     return True
    # return False
    
    # nki, nkj = ni.split_performed, nj.split_performed
    # nki_output_streams = ni.output_streams
    # nkj_input_streams = nj.input_streams
    
    # if nkj=="":
    #     return False
    # split_index = nkj.index('|')
    
    # nki_output_streams_of_interest = nkj_input_stream_of_interest = nkj[:split_index] + nkj[split_index+1:]
    if ni.output_streams == nj.input_streams:
        return True
    return False



def get_all_sharp_splits_and_compo_IDs_from_compo_ID(compo_ID):
    sharp_splits, compo_IDs = [], []
    for i in range(1, len(compo_ID)):
        new_compo_IDs = compo_ID[0:i], compo_ID[i:]
        compo_IDs += new_compo_IDs
        sharp_splits.append(new_compo_IDs[0] + '|' + new_compo_IDs[1])
    return sharp_splits, compo_IDs



def get_all_possible_sharp_split_nodes(node):
    node_split = node.split_performed
    curr_compo_IDs = list(node.output_streams)
    # print(curr_compo_IDs)
    ss_nodes = []
    # if node_split:
    #     split_index = node_split.index('|')
    #     curr_compo_IDs = [node_ID[:split_index], node_ID[split_index+1:]]
    #     ss_nodes = [node_ID]
    completed_compo_IDs = []
    # print(node.input_streams, node.output_streams, curr_compo_IDs)
    # print(node.ID+"\n")
    while curr_compo_IDs:
        cci = curr_compo_IDs.pop(0)
        for i in range(len(cci)):
            sharp_splits, compo_IDs = get_all_sharp_splits_and_compo_IDs_from_compo_ID(cci)
            for compo_ID in compo_IDs:
                if not compo_ID in completed_compo_IDs:
                    curr_compo_IDs.append(compo_ID)
                    completed_compo_IDs += compo_ID
            for sharp_split in sharp_splits:
                count = 0
                for ss_node in ss_nodes:
                    if sharp_split == ss_node.split_performed and node.output_streams==ss_node.input_streams:
                        count+=1
                if count == 0:
                    split_index = sharp_split.index('|')
                    additional_output_streams = [sharp_split[:split_index], sharp_split[split_index+1:]]
                    stream_split = additional_output_streams[0] + additional_output_streams[1]
                    # stream_split.remove("|")
                    prev_node = None
                    for nn in [node]+ss_nodes:
                        if stream_split in nn.output_streams:
                            prev_node = nn
                    # print("pn:"+prev_node.ID)
                    input_streams = prev_node.output_streams
                    new_node = DAGNode(split_performed=sharp_split,
                                       input_streams=input_streams,
                                       output_streams=set([stream for stream in input_streams
                                                      if not stream==stream_split]+additional_output_streams)
                                       )
                    # print([stream for stream in node.output_streams
                    #                if not stream==cci]+additional_output_streams)
                    
                    # print(sharp_split, additional_output_streams)
                    ss_nodes.append(new_node)
                    # print(new_node.ID)
    # print("\n\n")
    return ss_nodes



def get_cost_sharp_split(edge, map_dict, feed_stream, column_type='ShortcutColumn'):
    ni, nj = edge
    nki, nkj = ni.split_performed, nj.split_performed
    nsi, nsj = ni.output_streams, nj.output_streams
    
    
    # split_indices = nki.index('|'), nkj.index('|')
    # split_index = split_indices[1]
    
    
    # LHK_pointers = nkj[split_index-1:split_index], nkj[split_index+1:split_index+2]
    LHK_pointers = nj.LHK_pointers
    # print(edge, LHK_pointers)
    LHK = [map_dict[i] for i in LHK_pointers]
    Lr = Hr = 0.9999
    
    # compo_IDs_nki = nki[:split_indices[0]], nki[split_indices[0]+1:]
    
    
    # compo_IDs_nkj = nkj[:split_indices[1]], nkj[split_indices[1]+1:]
    # print(ni.ID, "\n", nj.ID, "\n\n")
    # print(nki, nkj, LHK_pointers, compo_IDs_nki)
    
    compo_ID_of_D_in_stream = None
    # for compo_ID in compo_IDs_nki:
    for compo_ID in nj.input_streams:
        if LHK_pointers[0] in compo_ID or LHK_pointers[1] in compo_ID:
            compo_ID_of_D_in_stream = compo_ID
    
    D_in_stream = feed_stream.copy()
    D_in_stream.ID = compo_ID_of_D_in_stream
    D_in_stream.F_mol = 0
    feed_stream
    for k in compo_ID_of_D_in_stream:
        chem_ID_k = map_dict[k]
        D_in_stream.imol[chem_ID_k] = feed_stream.imol[chem_ID_k]
    
    # print(LHK)
    # D_in_stream.show()
    
    try:
        # import pdb
        # pdb.set_trace()
        F_V = D_in_stream.imol[LHK[0]]/sum([D_in_stream.imol[i.ID] for i in D_in_stream.vle_chemicals])
        F = add_flash_vessel(in_stream=D_in_stream,
                            V=F_V, 
                            ID=None,
                            P=101325./40., 
                            vessel_material='Stainless steel 316',)
        F.simulate()
        assert F.outs[0].imol[LHK[0]] > 0.99 * D_in_stream.imol[LHK[0]]
        assert F.outs[1].imol[LHK[1]] > 0.99 * D_in_stream.imol[LHK[1]]
        return F.utility_cost, F
    
    except:
        pass
    
    D = add_distillation_column(D_in_stream,
                                LHK=LHK, 
                                Lr=Lr, Hr=Hr,
                                column_type=column_type,
                                ID=None,
                                k=1.05, P=101325./40., 
                                is_divided=True,
                                partial_condenser=False,
                                vessel_material='Stainless steel 316',
                                )
    # D.show()
    # print(D.LHK)
    try:
        D.simulate()
    except RuntimeError as e:
        if 'cannot meet' in str(e):
            try:
                psd_units = mock_pressure_swing_distillation(D_in_stream, LHK=LHK, Ps=(101325, 20*101325))
                util_cost_tot = 0
                for u in psd_units:
                    u.simulate()
                    util_cost_tot += u.utility_cost
                # print(f'\nPSD used: {LHK}; cost={util_cost_tot}')
                return util_cost_tot, psd_units
            except(RuntimeError or ValueError or FloatingPointError) as e:
                # print((nki, nkj), str(e))
                try:
                    D = add_distillation_column(D_in_stream,
                                                LHK=LHK, 
                                                Lr=Lr, Hr=Hr,
                                                column_type=column_type,
                                                ID=None,
                                                k=1.05, P=101325., 
                                                is_divided=True,
                                                partial_condenser=False,
                                                vessel_material='Stainless steel 316',
                                                )
                # import pdb
                # pdb.set_trace()
                    D.simulate()
                except(RuntimeError or ValueError or FloatingPointError) as e:
                    # print((nki, nkj), str(e))
                    return 1e10, D
    except:
        try:
            D = add_distillation_column(D_in_stream,
                                        LHK=LHK, 
                                        Lr=Lr, Hr=Hr,
                                        column_type=column_type,
                                        ID=None,
                                        k=1.05, P=101325., 
                                        is_divided=True,
                                        partial_condenser=False,
                                        vessel_material='Stainless steel 316',
                                        )
        # import pdb
        # pdb.set_trace()
            D.simulate()
        except (RuntimeError or ValueError or FloatingPointError) as e:
            # print((nki, nkj), str(e))
            return 1e10, D
                
    return D.utility_cost, D



def generate_DAG_vle_sharp(in_stream, chem_IDs=None, include_infeasible_edges=False, column_type='ShortcutColumn', products=None, cutoff_massfrac=0.005):
    # chem_IDs = in_stream.products + in_stream.impurities
    
    tmo.settings.set_thermo(in_stream.chemicals)
    
    for i in in_stream.chemicals:
        if in_stream.imass[i.ID]/in_stream.F_mass<cutoff_massfrac:
            in_stream.imol[i.ID] = 0.
    
    if not chem_IDs:
        chem_IDs = [i.ID for i in get_vle_components_sorted(in_stream)]
    
    map_keys = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
    map_dict = {map_keys[i]:chem_IDs[i] for i in range(len(chem_IDs))}
    map_dict_rev = {chem_IDs[i]:map_keys[i] for i in range(len(chem_IDs))}
    # print(map_dict)
    start_node = DAGNode(split_performed = "",
                         input_streams = ["".join([i for i in list(map_dict.keys())])],
                         output_streams = ["".join([i for i in list(map_dict.keys())])])
    nodes_list = []
    # print(start_node.ID)
    temp_nodes = [start_node]
    
    while temp_nodes:
        # print(temp_nodes)
        # print(nodes_list)
        # print('\n')
        # for node in temp_nodes:
        node = temp_nodes.pop(0)
        # print(node.ID)
        temp_nodes += get_all_possible_sharp_split_nodes(node)
        # print(get_all_possible_sharp_split_nodes(node))
        # print(temp_nodes)
        # temp_nodes.remove(node)
        for tn in temp_nodes:
            if not tn in nodes_list:
                nodes_list.append(tn)
                temp_nodes.remove(tn)
            elif tn in nodes_list:
                temp_nodes.remove(tn)
            # if len(tn)==3:
            #     temp_nodes.remove(tn)
        
    nodes_list= [start_node] + nodes_list
    # nodes_list += [k+"|" for k in map_dict.keys()]
    # print(nodes_list)
    edges_dict = {}
    edges_units_dict = {}
    # print(nodes_list)
    for ni in nodes_list:
        for nj in nodes_list:
            nki, nkj = ni.split_performed, nj.split_performed
            nsi, nsj = ni.output_streams, nj.output_streams
            if not nki==nkj:
                # print(has_edge(ni, nj))
                if has_edge(ni, nj) and (ni.ID, nj.ID) not in edges_dict.keys():
                    # nki_to_use = nki
                    # if nki[0] == "|":
                    #     nki_to_use = nki[1:]
                    cost, new_units = get_cost_sharp_split((ni, nj), map_dict, in_stream, column_type)
                    
                    if cost == 1e10:
                        if include_infeasible_edges:
                            edges_dict[(ni.ID, nj.ID)] = cost
                    else:
                        edges_dict[(ni.ID, nj.ID)] = cost
                    
                    edges_units_dict[(ni.ID, nj.ID)] = new_units
                    
    edge_dict_keys = list(edges_dict.keys())
    # for i in nodes_list:
    #     print(i.ID)
    absolute_terminal_node_ins = nodes_list[-1].output_streams
    absolute_terminal_node = DAGNode(split_performed = "",
                         input_streams = absolute_terminal_node_ins,
                         output_streams = absolute_terminal_node_ins)
    for k,l in edge_dict_keys:
        for n in nodes_list:
            if l==n.ID:
                if n.output_streams == absolute_terminal_node_ins:
                    edges_dict[(n.ID, absolute_terminal_node.ID)] = 0
                
        # if len(k[1])==3:
            # edges_dict[(k[1], "A,B,C,D")] = 0
    
    nodes_dict = {}
    
    terminal_nodes = []
    
    for nnn in nodes_list:
        nodes_dict[nnn.ID] = nnn
        # print(nnn.output_streams, [map_dict_rev[p] for p in products])
        if np.array([map_dict_rev[p] in nnn.output_streams for p in products]).all():
            terminal_nodes.append(nnn.ID)
    
    return edges_dict, map_dict, nodes_dict, edges_units_dict, terminal_nodes
# #%% DAG - topological sort distillation-only example


# # feed_stream = APDStream(
# #     ID='AdAcG', # can customize this name; an auto-generated name will be given by default
# #     composition_dict = { # Keys: Chemicals; Use CAS IDs where unsure of names # Values: molar flows (kmol/h)
# #     'Water' : 1000,
# #     'AdipicAcid' : 20,
# #     'AceticAcid' : 20,
# #     'Glycerol' : 20,
# #     },
# #     products = ['AdipicAcid', 'AceticAcid', 'Glycerol'], # Chemicals; Use CAS IDs where unsure of names
# #     impurities = ['Water'] # Chemicals; Use CAS IDs where unsure of names
# #     ),


# tmo.settings.set_thermo(['Water', 
#                          'Ethanol', 
#                           # 'Hexane', 
#                           'Glycerol', 
#                          # 'AceticAcid',
#                           'AdipicAcid',
#                          ])
# # tmo.settings.set_thermo(['Water', 'Ethanol'])
# stream = tmo.Stream('stream')
# # stream.imass['Ethanol'] = 11.1
# stream.imol['Water'] = 100
# stream.imol['Ethanol'] = 5
# # stream.imol['Glycerol'] = 5
# # stream.imol['AdipicAcid'] = 5
# # stream.imass['LevulinicAcid'] = 10

# from biorefineries.corn.example_run import tea_1
# stream = tea_1.stream_to_separation
# print('\n\nInitialized stream.')

#%%

def get_valid_ID(ID):
    valid_ID = ''
    for i in ID:
        if i==' ':
            valid_ID += '__'
        elif i=='-':
            valid_ID += '_'
        else:
            valid_ID += i
    return valid_ID

solvent_prices = {solvent: 5. for solvent in solvent_IDs} # solvent price defaults to $5/kg
def perform_solvent_extraction(stream, solvent_ID, partition_data={}, T=None, P=None,
                               solvent_prices=solvent_prices):
    # try:
        # import pdb
        # pdb.set_trace()
        tmo.settings.set_thermo(list(stream.chemicals) + [solvent_ID])
        new_stream = tmo.Stream('new_stream')
        #!!!
        if T:
            stream.T = T
        if P:
            stream.P = P
            
        new_stream.T, new_stream.P = stream.T, stream.P
        for i in stream.chemicals:
            new_stream.imol[i.ID] = stream.imol[i.ID]
        solvent_price = 5.
        try:
            solvent_price = solvent_prices[solvent_ID]
        except:
            pass
        fresh_solvent_stream = tmo.Stream(f'fresh_stream_{get_valid_ID(solvent_ID)}',
                                          price=solvent_price)
        
        new_mixer = bst.Mixer(f'extraction_mixer_{get_valid_ID(solvent_ID)}',
                              ins=(new_stream, fresh_solvent_stream, ''),
                              outs=('to_extraction'))
        @new_mixer.add_specification(run=False)
        def new_mixer_spec():
            solvent_vol_req = 2.5*new_stream.ivol['Water']
            fresh_solvent_stream.ivol[solvent_ID] = max(0, solvent_vol_req - new_mixer.ins[2].ivol[solvent_ID])
            new_mixer._run()
        new_mixer.simulate() 
        # import pdb
        # pdb.set_trace()
        
        msms = None
        for N in [8, 7, 6, 5, 4, 3, 2, 1]:
            try:
                msms = bst.MultiStageMixerSettlers(ID=f'extraction_{get_valid_ID(solvent_ID)}', 
                                                   ins=new_mixer-0, thermo=new_stream.thermo, outs=(), N_stages=N, solvent_ID=solvent_ID,
                                                   partition_data = partition_data)
                msms.simulate()
                break
            except:
                pass
        
        return msms.extract, new_stream, [new_mixer, msms]
    # except:
    #     return None, None, None
    
def identical_streams(stream1, stream2, mol_compo_sig_figs=2, F_mol_sig_figs=0):
    if stream1.F_mol==0 or stream2.F_mol==0:
        return False
    for i in stream1.chemicals:
        if round(stream1.imol[i.ID]/stream1.F_mol, mol_compo_sig_figs)==\
            round(stream2.imol[i.ID]/stream2.F_mol, mol_compo_sig_figs)\
            and round(stream1.F_mol/100, F_mol_sig_figs)==\
                round(stream2.F_mol/100, F_mol_sig_figs):
                    
                    # return True
                    pass
        else:
            return False
    return True

# def identical_streams(stream1, stream2, mass_compo_sig_figs=2, F_mass_sig_figs=2, cutoff_massfrac=0.01):
#     if stream1.F_mass==0 or stream2.F_mass==0:
#         return False
#     if not float(f'{stream1.F_mass:.{F_mass_sig_figs}g}')==\
#         float(f'{stream2.F_mass:.{F_mass_sig_figs}g}'):
#             return False
#     for i in stream1.chemicals:
#         if stream1.imass[i.ID]/stream1.F_mass >= cutoff_massfrac or\
#             stream2.imass[i.ID]/stream1.F_mass >= cutoff_massfrac:
#             # if round(stream1.imass[i.ID]/stream1.F_mass, mass_compo_sig_figs)==\
#             #     round(stream2.imass[i.ID]/stream2.F_mass, mass_compo_sig_figs):
#             print(i.ID, float(f'{stream1.imass[i.ID]/stream1.F_mass:.{mass_compo_sig_figs}g}'),
#                 float(f'{stream2.imass[i.ID]/stream2.F_mass:.{mass_compo_sig_figs}g}'))
#             if float(f'{stream1.imass[i.ID]/stream1.F_mass:.{mass_compo_sig_figs}g}')==\
#                 float(f'{stream2.imass[i.ID]/stream2.F_mass:.{mass_compo_sig_figs}g}'):
#                         # return True
#                         pass
#             else:
#                 return False
#     return True


def connect_units(units, stream):
    
    all_streams = [stream]
    for u in units:
        all_streams += list(u.ins)
        all_streams += list(u.outs)
    sinkless_streams = [s for s in all_streams if not s.sink]
    sourceless_streams = [s for s in all_streams if not s.source]
    
    for s1 in sinkless_streams:
        for s2 in sourceless_streams:
            if identical_streams(s1, s2):
                if s2.sink:
                    s2.sink.ins[s2.sink.ins.index(s2)] = s1
                # print(s1, s2, s1.sink, s2.sink, s1.source, s2.source)

def remove_trace_chemicals(stream, trace_massfrac_threshold=0.01):
    for i in stream.chemicals:
        if stream.imass[i.ID]/stream.F_mass < trace_massfrac_threshold:
            stream.imol[i.ID] = 0.

#%% Run
def get_separation_units(stream, products=[], plot_graph=False, print_progress=False, 
                         connect_path_units=True, simulate_again_after_connecting=False,
                         include_infeasible_edges=False, save_DAG=False,
                         solvent_prices=solvent_prices):
 
    
    extract, stream_for_DAG, msms = None, stream, None
    
    if print_progress:
        print('Attempting crystallization ...')
    
    stream_copy = Stream('stream_copy')
    stream_copy.copy_like(stream)
    # stream_for_DAG.show()
    pre_DAG_path_units = add_crystallizer_filter_dryer(in_stream=stream_copy, solute=products[0],
                                                     IDs=[f'{stream.ID}_crystallizer', f'{stream.ID}_filter',
                                                          f'{stream.ID}_dryer'])
    
    
    
    add_pre_DAG_path_units = False
    
    if pre_DAG_path_units[0].effective_recovery>=0.2:
        add_pre_DAG_path_units = True
        pre_DAG_path_units[0].ins[0] = stream
        pre_DAG_path_units[0].simulate()
        stream_for_DAG = pre_DAG_path_units[1].outs[1]
    
    # print('\n\n\nStream for DAG\n')
    # stream_for_DAG.show()
    has_products = False
    for p in products:
        if stream_for_DAG.imol[p]/stream_for_DAG.F_mol >= 0.01:
            has_products = True
    
    if has_products:
        if print_progress:
            print('Running solvents barrage ...')
        
        Ts = list(np.linspace(10+273.15, 90+273.15, 10))
        Ts.reverse()
        
        for T in Ts:
            candidate_solvents_dict, results_df = get_candidate_solvents_ranked(stream=stream, 
                                          solute_ID=products[0], 
                                          impurity_IDs=[c.ID for c in stream_for_DAG.chemicals if not c.ID in products],
                                          T=T,
                                          plot_Ks=False)
            
            
            extract, stream_for_DAG, msms = None, stream, None
            
            # print(list(candidate_solvents_dict.keys()))
            
            if list(candidate_solvents_dict.keys()): # if a candidate solvent is found
                if print_progress:
                    print(f'Performing primary extraction at{T-273.15} degC using solvent: {list(candidate_solvents_dict.keys())[0]} ...')
                stream_for_DAG, new_stream, msms = perform_solvent_extraction(stream, 
                                                                              list(candidate_solvents_dict.keys())[0], list(candidate_solvents_dict.values())[0],
                                                                              solvent_prices=solvent_prices,
                                                                              T=T)
                products.append(list(candidate_solvents_dict.keys())[0])
                break
            # msms[0].show(N=100)
            # msms[1].show(N=100)
    
        # %%
        
        if print_progress:
            stream.show('cwt100')
            stream_for_DAG.show('cwt100')
        
        
        # remove_trace_chemicals = True
        
        # if remove_trace_chemicals:
        #     for i in stream_for_DAG.chemicals:
        #         i_ID = i.ID
                # stream_for_DAG.imol['Water'] = 0.
                # if stream_for_DAG.imass[i_ID]/stream_for_DAG.F_mass < 0.005:
                #     stream_for_DAG.imass[i_ID] = 0.
        remove_trace_chemicals(stream_for_DAG)
        if print_progress:
            print('Generating graph ...')
        edges_dict, map_dict, nodes_dict, edges_units_dict, terminal_nodes = generate_DAG_vle_sharp(stream_for_DAG,
                                                                  column_type='BinaryDistillation',
                                                                  include_infeasible_edges=include_infeasible_edges,
                                                                  products=products)
        
        # # if save_DAG:
        # with open('DAG.txt', 'w') as f:
        #     for k, v in edges_dict.items():
        #         f.write(str(k[0]) + "    " + str(k[1]) + "    " + str(v) + "\n")
                

        # G=nx.read_weighted_edgelist("./DAG.txt", delimiter="    ")
        
        G = nx.Graph()
        for k,v in edges_dict.items():
            G.add_edge(str(k[0]), str(k[1]), weight=v)
            
        # for (i,j,d) in G.edges(data=True):
        #     print(i,j,d['weight'])
            
        edges_dict_keys = list(edges_dict.keys())
        
        # print(terminal_nodes)
        # print('nodes:')
        # print(G.nodes)
        # print('\n')
        # print(edges_dict_keys[0][0], edges_dict_keys[-1][-1])
        paths = [nx.shortest_path(G, edges_dict_keys[0][0], tn, weight='weight') for tn in terminal_nodes if tn in G.nodes]
        
        # path_lengths = [path_weight(G, path, weight='weight') for path in paths]
        
        def get_path_length(path):
            return path_weight(G, path, weight='weight')
        
        # for p in range(len(paths)):
        #     print(paths[p], path_lengths[p])
        
        paths.sort(key=lambda i: get_path_length(i))
        path = paths[0]
        
        path_edges = list(zip(path,path[1:]))
        
        if print_progress:
            print(path_edges)
            print()
        
        
        #%% Plot
        if plot_graph:
            print("Plotting graph ...")
            edges_dict_copy = deepcopy(edges_dict)
            for k in edges_dict_copy.keys():
                if edges_dict_copy[k]==1e10:
                    edges_dict_copy[k]='inf'
                else: edges_dict_copy[k] = np.round(edges_dict_copy[k], 2)
                
            
            plt.figure(figsize=(40,40))
            
            pos = nx.circular_layout(G, scale=20,)
            # pos = nx.multipartite_layout(G)
            
            # Draw the entire graph
            nx.draw(G,pos,with_labels = True)
            
            # Draw all edge labels
            nx.draw_networkx_edge_labels(
                G, pos,
                edge_labels=edges_dict_copy,
                font_color='red'
            )
            
            # Highlight shortest path
            nx.draw_networkx_nodes(G,pos,nodelist=path,node_color='r')
            nx.draw_networkx_edges(G,pos,edgelist=path_edges,edge_color='r',width=10)
            
            
            plt.axis('equal')
            plt.show()
    
    
        #%% Create system
        path_units = []
        if msms:
            path_units.extend(msms)
        for edge in path_edges:
            try:
                edge_units = edges_units_dict[edge]
                if type(edge_units)==list or type(edge_units)==tuple:
                    # print(edge_units)
                    for eu in edge_units:
                        path_units.append(eu)
                else:
                    path_units.append(edge_units)
            except:
                pass
        
        # if connect_path_units:
        #     connect_units(path_units, stream)
        
        
        if add_pre_DAG_path_units:
            if connect_path_units:
                connect_units(pre_DAG_path_units + path_units, stream)
                
                if simulate_again_after_connecting:
                    for u in path_units:
                        u.simulate()
            return pre_DAG_path_units + path_units
        
        else:
            if connect_path_units:
                connect_units(path_units, stream)
                
                if msms:
                    solvent_ID = msms[1].solvent_ID
                    for u in path_units:
                        for s in list(u.outs):
                            if not s.sink:
                                # print(tmo.settings.get_thermo())
                                # s.show(N=100)
                                if s.imol[solvent_ID]/s.F_mol >= 0.95:
                                    extraction_mixer = msms[0]
                                    s-2-extraction_mixer
                                    extraction_mixer.simulate()
                if simulate_again_after_connecting:
                    for u in path_units:
                        u.simulate()
        # else:
            return path_units
        
    else:
        return pre_DAG_path_units    