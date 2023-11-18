# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 21:26:06 2023

@author: sarangbhagwat
"""

import numpy as np
from matplotlib import pyplot as plt
import biosteam as bst
import thermosteam as tmo

from biorefineries import lactic, sugarcane, cellulosic
from biorefineries.cornstover import CellulosicEthanolTEA

from warnings import filterwarnings
filterwarnings('ignore')

flowsheet = bst.main_flowsheet
u = flowsheet.unit
s = flowsheet.stream

#%% Consolidate chemicals
brs = [lactic, sugarcane]

chems_brs_compiled = [br._chemicals.create_chemicals() for br in brs]

chems_brs = [tmo.Chemicals(cbr) for cbr in chems_brs_compiled]


chems_flattened = tmo.Chemicals(chems_brs[0])
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
for i in list(chems_brs_compiled[0].chemical_groups):
    chems_flattened.define_group(i, [c.ID for c in chems_brs_compiled[0].__dict__[i]])

#%% Set thermo
tmo.settings.set_thermo(chems_flattened)

#%% Create SystemFactory

@bst.SystemFactory(ID = 'final_sys')
def create_final_sys(ins, outs):

    # Corn stover pretreatment
    pretreatment_sys = cellulosic.systems.pretreatment.create_dilute_acid_pretreatment_system()
    
    # Sugarcane juicing 
    juicing_sys = sugarcane.create_juicing_system_up_to_clarification()
    X210 = bst.Unit('X210', ins=juicing_sys-0, outs='hydrolyzed_juice_A')
    
    @X210.add_specification(run=False)
    def X210_spec():
        X210.outs[0].copy_like(X210.ins[0])
        X210.outs[0].imol['Glucose'] = 2*(X210.ins[0].imol['Sucrose'] - 1e-5)
        X210.outs[0].imol['Sucrose'] = 1e-5
        X210.outs[0].imol['Furfural'] = 1e-5
    
    # Sugars-to-ethanol
    ethanol_conv_sys = sugarcane.create_sucrose_to_ethanol_system()
    
    
    _cell_mass_split, _gypsum_split, _AD_split, _MB_split = lactic.get_splits()

    # Saccharification & lactic conversion sys
    lactic.create_conversion_process(kind='SHF', feed=pretreatment_sys-0, cell_mass_split=_cell_mass_split)
    lactic_conv_sys = bst.main_flowsheet('conversion_sys',)
    
    u.R301.allow_dilution = True
    
    u.S302.ID = 'S351'
        
    # Split sugarcane juice between ethanol and lactic
    S220 = bst.Splitter('S220', ins=(X210-0,), outs=('juice_to_ethanol', 'juice_to_lactic_acid'),
                        split=0.5)
    
    # Split corn stover saccharified slurry between ethanol and lactic
    S320 = bst.Splitter('S320', ins=(u.S301-1,), outs=('slurry_to_ethanol', 'slurry_to_lactic_acid'),
                        split=0.5)
    
    # Mix slurry and juice to divert to ethanol
    M250 = bst.Mixer('M250', ins=(S220-0, S320-0), outs=('mixed_saccharified_slurry_and_juice_to_ethanol'))
    M250-0-0-ethanol_conv_sys
    
    # Mix slurry and juice to divert to lactic
    M350 = bst.Mixer('M350', ins=(S220-1, S320-1), outs=('mixed_saccharified_slurry_and_juice_to_lactic'))
    M350-0-0-u.S351
    
    # Lactic separation
    lactic.create_separation_process(feed=u.R301_P1-0, 
                                     cell_mass_split=_cell_mass_split, 
                                     gypsum_split=_gypsum_split)
    lactic_sep_sys = bst.main_flowsheet('separation_sys')
    u.F402_P.outs[0].ID = 'lactic_acid'
    
    #%% New sys
    new_sys = bst.System.from_units('sc_lactic', units = pretreatment_sys.units +\
                                    [X210, S220, M250, S320, M350,] +\
                                    juicing_sys.units + ethanol_conv_sys.units + lactic_conv_sys.units +\
                                    lactic_sep_sys.units)
    # flowsheet = bst.main_flowsheet
    
    #%% Simulate
    new_sys.simulate()
    
    #%% Product criteria
    products_dict = {'Ethanol': 0.95, 'LacticAcid': 0.85}
    
    #%% Identify product streams
    product_streams = []
    for p_ID, p_wt_purity in products_dict.items():
        product_streams += [i for i in new_sys.products if i.F_mol and i.imass[p_ID]/i.F_mass >= p_wt_purity]
    
    #%% Create product storage
    
    
    #%% Waste criteria (besides price=0)
    liquid_waste_min_water = 0.5 
    solid_waste_water_less_than = 1. - liquid_waste_min_water
    
    #%% Identify waste streams
    
    liquid_waste_streams = [i for i in new_sys.products if (not i in product_streams) and i.F_mol and i.imass['Water']/i.F_mass >= liquid_waste_min_water]
    solid_waste_streams = [i for i in new_sys.products if (not i in product_streams) and i.F_mol and i.imass['Water']/i.F_mass < solid_waste_water_less_than]
    
    #%% Create waste treatment sys
    M501 = bst.units.Mixer('M501', ins=liquid_waste_streams)
    
    wastewater_treatment_sys = bst.create_wastewater_treatment_system(
        ins=M501-0,
        mockup=True,
        area=500,
    )
    
    # Mix solid wastes to boiler turbogenerator
    M510 = bst.units.Mixer('M510', ins=solid_waste_streams, 
                            outs='wastes_to_boiler_turbogenerator')
    
    MX = bst.Mixer(400, ['', ''])
    
    
    #%% Create facilities
    mixed_feeds = tmo.Stream('mixed_feeds')
    mixed_feeds.mix_from([s.sugarcane, s.cornstover])
    cellulosic.create_facilities(
        solids_to_boiler=M510-0,
        gas_to_boiler=wastewater_treatment_sys-0,
        process_water_streams=[
         s.imbibition_water,
         s.rvf_wash_water,
         s.dilution_water,
         # s.makeup_water,
         # s.fire_water,
         # s.boiler_makeup_water,
         # s.CIP,
         # s.recirculated_chilled_water,
         # s.s.3,
         # s.cooling_tower_makeup_water,
         # s.cooling_tower_chemicals,
         ],
        feedstock=mixed_feeds,
        RO_water=wastewater_treatment_sys-2,
        recycle_process_water=MX-0,
        BT_area=700,
        area=900,
    )

#%% Create final sys
final_sys = create_final_sys()
flowsheet = bst.main_flowsheet
u = flowsheet.unit
s = flowsheet.stream

feedstocks = [s.sugarcane, s.cornstover]
u.BT701.ID = 'BT701'
u.CT901.ID = 'CT801'
u.CWP901.ID = 'CWP802'
u.CIP901.ID = 'CIP901'
u.ADP901.ID = 'ADP902'
u.FWT901.ID = 'FWT903'
u.PWC901.ID = 'PWC904'

BT = flowsheet('BT')
BT.natural_gas_price = 0.2527

u.C501.moisture_content = 0.65 # running into infeasible moisture content error at default moisture_content of 0.79

#%% Create TEA object
get_flow_dry_tpd = lambda: sum([feedstock.F_mass-feedstock.imass['H2O'] for feedstock in feedstocks])*24/907.185
final_tea = CellulosicEthanolTEA(system=final_sys, IRR=0.10, duration=(2016, 2046),
        depreciation='MACRS7', income_tax=0.21, 
        # operating_days=0.9*365,
        operating_days = 0.9*365.,
        lang_factor=None, construction_schedule=(0.08, 0.60, 0.32),
        startup_months=3, startup_FOCfrac=1, startup_salesfrac=0.5,
        startup_VOCfrac=0.75, WC_over_FCI=0.05,
        finance_interest=0.08, finance_years=10, finance_fraction=0.4,
        # biosteam Splitters and Mixers have no cost, 
        # cost of all wastewater treatment units are included in WWT_cost,
        # BT is not included in this TEA
        OSBL_units=(
                    u.U501,
                    # u.T601, u.T602, 
                    # u.T601, u.T602, u.T603, u.T604,
                    # u.T606, u.T606_P,
                    u.BT701, u.CT801, u.CWP802, u.CIP901, u.ADP902, u.FWT903, u.PWC904,
                    ),
        warehouse=0.04, site_development=0.09, additional_piping=0.045,
        proratable_costs=0.10, field_expenses=0.10, construction=0.20,
        contingency=0.10, other_indirect_costs=0.10, 
        labor_cost=3212962*get_flow_dry_tpd()/2205,
        labor_burden=0.90, property_insurance=0.007, maintenance=0.03,
        steam_power_depreciation='MACRS20', boiler_turbogenerator=u.BT701)

for unit in final_sys.cost_units:
    if unit.utility_cost == None:
        unit._utility_cost = 0
        
#%% Simulate and perform TEA
s.lactic_acid.price = 1.5
s.ethanol.price = 0.75
final_sys.simulate()
print(final_tea.solve_IRR())

#%% Utils
S220, S320 = u.S220, u.S320
def load_substrate_splits_and_simulate_get_IRR(juice_split, slurry_split): # ethanol:lactic
    S220.split, S320.split = juice_split, slurry_split
    return simulate_get_IRR()

sugarcane, cornstover = s.sugarcane, s.cornstover
def load_sugarcane_feed_F_mass(F_mass):
    sugarcane.F_mass = F_mass
    
def load_cornstover_feed_F_mass(F_mass):
    cornstover.F_mass = F_mass

def load_total_feed_capacity_and_composition_and_simulate_get_IRR(tot_cap=440000, comp=0.5):
    load_sugarcane_feed_F_mass(tot_cap*comp)
    load_cornstover_feed_F_mass(tot_cap*(1.-comp))
    return simulate_get_IRR()

def set_sugarcane_price(sugarcane_stream):
    sugarcane_stream.price = 0.03455 + 0.01*max(0, sugarcane_stream.F_mass/333334.20-1) # placeholder 

def set_cornstover_price(cornstover_stream):
    cornstover_stream.price = 0.05159 + 0.01*max(0, cornstover_stream.F_mass/104229.16-1) # placeholder 

def set_lactic_acid_price(lactic_acid_stream):
    lactic_acid_stream.price =  1.5 - 0.01*max(0, lactic_acid_stream.F_mass/27177.076-1) # placeholder 

def set_ethanol_price(ethanol_stream):
    ethanol_stream.price =  0.75 - 0.01*max(0, ethanol_stream.F_mass/17634.269-1) # placeholder 
    
lactic_acid, ethanol = s.lactic_acid, s.ethanol

def simulate_get_IRR():
    set_sugarcane_price(sugarcane)
    set_cornstover_price(cornstover)
    set_lactic_acid_price(lactic_acid)
    set_ethanol_price(ethanol)
    final_sys.simulate()
    return final_tea.solve_IRR()

R301 = u.R301
def get_required_lactic_inlet_sugars_concentration(target_titer=97.5):
    return target_titer/(R301.cofermentation_rxns[0].X*180.16/180.16)

#%% Evaluate across juice and slurry diversion
eval_diversion_space = False
if eval_diversion_space:
    juice_splits = np.linspace(0.1, 0.9, 5)
    slurry_splits = np.linspace(0.1, 0.9, 5)
    IRRs = []
    
    for js in juice_splits:
        IRRs.append([])
        for ss in slurry_splits:
            IRRs[-1].append(load_substrate_splits_and_simulate_get_IRR(js, ss))

    load_substrate_splits_and_simulate_get_IRR(0.5, 0.5)
    
    #%% Plot
    X, Y = np.meshgrid(slurry_splits, juice_splits)
    Z = np.array(IRRs)
    fig,ax=plt.subplots(1,1)
    cp = ax.contourf(X, Y, Z, levels=50)
    fig.colorbar(cp) # Add a colorbar to a plot
    ax.set_title('Filled Contours Plot')
    #ax.set_xlabel('x (cm)')
    ax.set_ylabel('y (cm)')
    plt.show()

#%% Evaluate across sugarcane and cornstover feed rates
eval_feed_capacity_space = True
if eval_feed_capacity_space:
    sugarcane_rates = np.linspace(333334*0.5, 333334*2, 5)
    cornstover_rates = np.linspace(104229*0.5, 104229*2, 5)
    IRRs = []
    
    for sr in sugarcane_rates:
        IRRs.append([])
        for cr in cornstover_rates:
            load_sugarcane_feed_F_mass(sr)
            load_cornstover_feed_F_mass(cr)
            IRRs[-1].append(simulate_get_IRR())

    #%% Plot
    X, Y = np.meshgrid(cornstover_rates, sugarcane_rates,)
    Z = np.array(IRRs)
    fig,ax=plt.subplots(1,1)
    cp = ax.contourf(X, Y, Z, levels=50)
    fig.colorbar(cp) # Add a colorbar to a plot
    ax.set_title('Filled Contours Plot')
    #ax.set_xlabel('x (cm)')
    ax.set_ylabel('y (cm)')
    plt.show()
    
#%% Evaluate across total feed capacity and feed sugarcane:cornstover ratio
eval_feed_space = False
if eval_feed_space:
    feed_caps = np.linspace(400000*0.25, 400000, 5)
    feed_mixes = np.linspace(0.3, 0.99, 6)
    IRRs = []
    
    for fc in feed_caps:
        IRRs.append([])
        for fm in feed_mixes:
            IRRs[-1].append(load_total_feed_capacity_and_composition_and_simulate_get_IRR(fc, fm))
            print(fc, fm, IRRs[-1][-1])

    #%% Plot
    X, Y = np.meshgrid(feed_mixes, feed_caps)
    Z = np.array(IRRs)
    fig,ax=plt.subplots(1,1)
    cp = ax.contourf(X, Y, Z, levels=50)
    fig.colorbar(cp) # Add a colorbar to a plot
    ax.set_title('Filled Contours Plot')
    #ax.set_xlabel('x (cm)')
    ax.set_ylabel('y (cm)')
    plt.show()
    