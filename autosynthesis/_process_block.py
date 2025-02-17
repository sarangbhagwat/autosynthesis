# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2022-, Sarang Bhagwat <sarangb2@illinois.edu>
# 
# This module is under the UIUC open-source license. See 
# github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE.txt
# for license details.
"""
Created on Mon Oct 14 14:54:32 2024

@author: sarangbhagwat
"""
import biosteam as bst

__all__ = ('ProcessBlock',)

CEPCI_by_year = bst.units.design_tools.cost_index.CEPCI_by_year

GDP_index = { # Dictionary of GDP indices
             2007: 0.961,
             2008: 0.990,
             2010:1.012 / 0.990
             }

chem_index = { # Dictionary of chemical indices
                    2010: 82.2,
                    2011: 79.5,
                    2012: 83.7,
                    2013: 87.9,
                    2014: 91.3,
                    2015: 93.1,
                    2016: 88.8,
                    2017: 92.7,
                    2018: 93.3,
                    2019: 97.0,
                    2020: 100.2,
                    2021: 112.0,
                    2022: 125.829,
                    }

class ProcessBlock():
    
    def __init__(self, ID, 
                 create_function, 
                 base_TEA_year,
                 inlets={}, 
                 outlets={},
                 boiler=[],
                 wastewater=[],
                 ignored_HXN=[],
                 N_ins=None,
                 N_outs=None,
                 ):
        self.ID = ID
        self.create_function = create_function
        self.base_TEA_year = base_TEA_year
        self.N_ins = N_ins
        self.N_outs = N_outs
        self.inlets = inlets
        self.outlets = outlets
        self.boiler = boiler
        self.wastewater = wastewater
        self.ignored_HXN = ignored_HXN
        self.flowsheet = None
        self.system = None
        
        self._TEA_year = base_TEA_year
        
    def create(self, inlets={}, outlets={}):
        # ins = [''] * self.N_ins
        # for stream_name, index in self.inlets.items():
        #     ins[index] = inlets[stream_name]
        # outs = [''] * self.N_outs
        # for stream_name, index in self.outlets.items():
        #     outs[index] = outlets[stream_name]
        
        self.system = system = self.create_function(ID=self.ID)
        self.flowsheet = system.flowsheet
    
    def inlet(self, name):
        return self.system.ins[self.inlets[name]]
    
    def outlet(self, name):
        return self.system.outs[self.outlets[name]]
    
    def connect(self, name_outlet, receiving_process_block, name_inlet):
        # print(self.outlet(name_outlet), receiving_process_block.inlets[name_inlet], receiving_process_block.inlet(name_inlet).sink)
        # self.outlet(name_outlet)-receiving_process_block.inlets[name_inlet]-receiving_process_block.inlet(name_inlet).sink
        inlet_stream = receiving_process_block.system.ins[receiving_process_block.inlets[name_inlet]]
        sink_unit_ins_index = receiving_process_block.inlet(name_inlet).sink.ins.index(inlet_stream)
        self.outlet(name_outlet)-sink_unit_ins_index-receiving_process_block.inlet(name_inlet).sink
        
    def make_all_possible_connections(self, receiving_process_block):
        # out_edges = self._out_edges
        # in_edges = receiving_process_block._acceptable_in_edges
        # for name in set(out_edges).intersection(set(in_edges)):
        #    self.connect(name, receiving_process_block, name) 

        outlets = self.outlets
        inlets = receiving_process_block.inlets
        for name in set(outlets.keys()).intersection(set(inlets.keys())):
            self.connect(name, receiving_process_block, name) 
    
    @property
    def out_edges(self):
        return list(self.outlets.keys())
    
    @property
    def acceptable_in_edges(self):
        return list(self.inlets.keys())
    
    @property
    def TEA_year(self):
        return self._TEA_year
    
    @TEA_year.setter
    def TEA_year(self, new_TEA_year):
        curr_TEA_year = self._TEA_year
        system = self.system
        conversion_factor = 1
        if curr_TEA_year<2010:
            conversion_factor = (GDP_index[2010]/GDP_index[curr_TEA_year]) *\
                (chem_index[new_TEA_year]/chem_index[2010])
        else:
            conversion_factor = chem_index[new_TEA_year]/chem_index[curr_TEA_year]
        for i in system.ins: i.price *= conversion_factor
        for i in system.outs: i.price *= conversion_factor
        bst.settings.CEPCI = CEPCI_by_year[new_TEA_year]
        self._TEA_year = new_TEA_year
