# -*- coding: utf-8 -*-
"""
Created on Thu Nov 24 17:23:33 2022

@author: sarangbhagwat
"""
import biosteam as bst
import thermosteam as tmo
from .units import WastewaterSystemCost
Stream = tmo.Stream

def create_wastewater_system(wastewater_streams=[], 
                             solid_waste_streams=[], 
                             price={'Caustics':0.262790704}):
    # %% 
    
    # =============================================================================
    # Wastewater treatment streams
    # =============================================================================
    
    # For aerobic digestion, flow will be updated in AerobicDigestion
    air_lagoon = Stream('air_lagoon', phase='g', units='kg/hr')
    
    # To neutralize nitric acid formed by nitrification in aerobic digestion
    # flow will be updated in AerobicDigestion
    # The active chemical is modeled as NaOH, but the price is cheaper than that of NaOH
    aerobic_caustic = Stream('aerobic_caustic', units='kg/hr', T=20+273.15, P=2*101325,
                              price=price['Caustics'])
    
    # =============================================================================
    # Wastewater treatment units
    # =============================================================================
    
    # Mix waste liquids for treatment
    M501 = bst.units.Mixer('M501', ins=wastewater_streams)
    
    
    # This represents the total cost of wastewater treatment system
    WWT_cost = WastewaterSystemCost('WWTcost501', ins=M501-0)
    
    # R501 = units.AnaerobicDigestion('R501', ins=WWT_cost-0,
    #                                 outs=('biogas', 'anaerobic_treated_water', 
    #                                       'anaerobic_sludge'),
    #                                 reactants=soluble_organics,
    #                                 split=find_split(splits_df.index,
    #                                                  splits_df['stream_611'],
    #                                                  splits_df['stream_612'],
    #                                                  chemical_groups),
    #                                 T=35+273.15)
    
    R501 = bst.AnaerobicDigestion('R501', ins=WWT_cost-0,
                                    outs=('biogas', 'anaerobic_treated_water', 
                                          'anaerobic_sludge'),
                                    # reactants=soluble_organics,
                                    # sludge_split=find_split(splits_df.index,
                                    #                  splits_df['stream_611'],
                                    #                  splits_df['stream_612'],
                                    #                  chemical_groups),
                                    # T=35+273.15,
                                    )

    # Mix recycled stream and wastewater after R501
    M502 = bst.units.Mixer('M502', ins=(R501-1, ''))

    R502 = bst.AerobicDigestion('R502', ins=(M502-0, 
                                                air_lagoon, aerobic_caustic,
                                               ),
                                  outs=('aerobic_vent', 'aerobic_treated_water', 
                                        # 'sludge',
                                        ),
                                  )
    
    # Membrane bioreactor to split treated wastewater from R502
    S501 = bst.units.Splitter('S501', ins=R502-1, outs=('membrane_treated_water', 
                                                        'membrane_sludge'),
                              # split=find_split(splits_df.index,
                              #                  splits_df['stream_624'],
                              #                  splits_df['stream_625'],
                              #                  chemical_groups),
                              )
    
    S501.line = 'Membrane bioreactor'
    
    # Recycled sludge stream of memberane bioreactor, the majority of it (96%)
    # goes to aerobic digestion and the rest to sludge holding tank then to BT
    S502 = bst.units.Splitter('S502', ins=S501-1, outs=('to_aerobic_digestion', 
                                                        'to_boiler_turbogenerator'),
                              split=0.96)
    
    M503 = bst.units.Mixer('M503', ins=(S502-0, 'centrate'), outs=1-M502)
    
    # Mix anaerobic and 4% of membrane bioreactor sludge
    M504 = bst.units.Mixer('M504', ins=(R501-2, S502-1))
    
    # Sludge centrifuge to separate water (centrate) from sludge
    S503 = bst.units.Splitter('S503', ins=M504-0, outs=(1-M503, 'sludge'),
                              # split=find_split(splits_df.index,
                              #                  splits_df['stream_616'],
                              #                  splits_df['stream_623'],
                              #                  chemical_groups),
                              )
    S503.line = 'Sludge centrifuge'
    
    # Reverse osmosis to treat membrane separated water
    S504 = bst.units.Splitter('S504', ins=S501-0, outs=('discharged_water', 'waste_brine'),
                              # split=find_split(splits_df.index,
                              #                  splits_df['stream_626'],
                              #                  splits_df['stream_627'],
                              #                  chemical_groups),
                              )
    S504.line = 'Reverse osmosis'
    
    # Mix solid wastes to boiler turbogenerator
    M505 = bst.units.Mixer('M505', ins=solid_waste_streams,
                            outs='wastes_to_boiler_turbogenerator')
    
    
    WWT_group = bst.UnitGroup('WWT_group', 
                                   units=(M501, WWT_cost,R501, M502, R502,
                                          S501, S502, M503, M504, S503, S504,
                                          M505,))
    return WWT_group