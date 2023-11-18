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
    pretreatment_sys = cellulosic.systems.pretreatment.create_dilute_acid_pretreatment_system()
    
    juicing_sys = sugarcane.create_juicing_system_up_to_clarification()
    X210 = bst.Unit('X210', ins=juicing_sys-0, outs='hydrolyzed_juice_A')
    
    @X210.add_specification(run=False)
    def X210_spec():
        X210.outs[0].copy_like(X210.ins[0])
        X210.outs[0].imol['Glucose'] = 2*(X210.ins[0].imol['Sucrose'] - 1e-5)
        X210.outs[0].imol['Sucrose'] = 1e-5
        X210.outs[0].imol['Furfural'] = 1e-5
        
    ethanol_conv_sys = sugarcane.create_sucrose_to_ethanol_system()
    
    _cell_mass_split, _gypsum_split, _AD_split, _MB_split = lactic.get_splits()
    
    
    S220 = bst.Splitter('S220', ins=(X210-0,), outs=('juice_to_ethanol', 'juice_to_lactic_acid'),
                        split=0.5)
    S220-0-0-ethanol_conv_sys
    
    M220 = bst.Mixer('M220', ins=(S220-1, pretreatment_sys-0), outs=('mixed_juice_and_pretreated_biomass_to_lactic'))
    
    lactic.create_conversion_process(kind='SSCF', feed=M220-0)
    lactic_conv_sys = bst.main_flowsheet('conversion_sys')
       
    lactic.create_separation_process(feed=lactic_conv_sys.outs[0], 
                                     cell_mass_split=_cell_mass_split, 
                                     gypsum_split=_gypsum_split)
    lactic_sep_sys = bst.main_flowsheet('separation_sys')
    
    #%% New sys
    new_sys = bst.System.from_units('sc_lactic', units = pretreatment_sys.units + [S220, M220, X210] + juicing_sys.units + ethanol_conv_sys.units + lactic_conv_sys.units + lactic_sep_sys.units)
    flowsheet = bst.main_flowsheet
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
    s = flowsheet.stream
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
        feedstock=s.sugarcane,
        RO_water=wastewater_treatment_sys-2,
        recycle_process_water=MX-0,
        BT_area=700,
        area=900,
    )

#%% Create final sys
final_sys = create_final_sys()

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

u.C501.moisture_content = 0.65

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
        
#%% Perform TEA
final_sys.products[4].price = 1.5
final_sys.products[5].price = 0.51
final_sys.simulate()
print(final_tea.solve_IRR())

#%% Evaluate across sugarcane diversion (ethanol:lactic)
sc_divs = np.linspace(0.05, 0.95, 10)

lactic_prods = []
ethanol_prods = []
IRRs = []
R301_input_sugars_concs = []
AOCs = []
TCIs = []
for sc_div in sc_divs:
    u.S220.split = sc_div
    final_sys.simulate()
    IRRs.append(final_tea.solve_IRR())
    lactic_prods.append(final_sys.products[4].F_mass * final_tea.operating_hours/1e3)
    ethanol_prods.append(final_sys.products[5].F_mass * final_tea.operating_hours/1e3)
    R301_input_sugars_concs.append(u.R301.ins[0].imass['Glucose', 'Xylose', 'Sucrose', 'Glucan', 'Xylan'].sum()/u.R301.ins[0].F_vol)
    AOCs.append(final_tea.AOC)
    TCIs.append(final_tea.TCI)

#%% Plot
plt.plot(sc_divs, ethanol_prods)
# plt.plot(sc_divs, ethanol_prods)