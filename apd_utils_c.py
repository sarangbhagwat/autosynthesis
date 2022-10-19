# -*- coding: utf-8 -*-
"""
Created on Mon Oct  3 17:21:51 2022

@author: sarangbhagwat
"""

import biosteam as bst
import thermosteam as tmo
import numpy as np
from warnings import filterwarnings
# load_set_and_get_corn_upstream_sys = load_set_and_get_corn_upstream_sys

filterwarnings('ignore')


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
                                      column_IDs=('temp_column_1', 'temp_column_2'),
                                      azeotrope_error_identifier_substring='cannot meet',
                                      target_column2_LK_recovery = 0.999,
                                      target_column2_ytop = 0.995,
                                      ):
    chems = stream.chemicals
    stream_LHK_only = stream.copy()
    stream_LK_only = tmo.Stream()
    stream_LK_only.imol[LHK[0]]
    stream_HK_only = tmo.Stream()
    
    # stream_LHK_only.P = Ps[0]
    for i in chems:
        if not i.ID in LHK:
            stream_LHK_only.imol[i.ID] = 0.
    T_bubble = stream_LHK_only.bubble_point_at_P(Ps[0]).T
    if T_bubble > chems[LHK[1]].Tb and T_bubble > chems[LHK[0]].Tb :
        stream.show('cmol100')
        raise RuntimeError(f'{LHK} forms a maximum-boiling azeotrope; {T_bubble} > {chems[LHK[0]].Tb} and {T_bubble} > {chems[LHK[1]].Tb}.)')
    
    
    temp_pump_1 = bst.Pump('temp_pump_1', ins=stream, P=Ps[0])
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
    
    temp_pump_2 = bst.Pump('temp_pump_2', ins=temp_column_1-0, P=Ps[1])
    
    
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
    
    temp_LK_mixer = bst.Mixer('temp_LK_mixer', ins=(temp_column_2-0))
    temp_LK_mixer.simulate()
    
    temp_HK_mixer = bst.Mixer('temp_HK_mixer', ins=(temp_column_1-1, temp_column_2-1))
    temp_HK_mixer.simulate()
    
    return (temp_pump_1, temp_column_1, temp_pump_2, temp_column_2, temp_LK_mixer, temp_HK_mixer)


#%% test TEA

