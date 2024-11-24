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

__all__ = ('ProcessBlock',)

class ProcessBlock():
    
    def __init__(self, ID, 
                 create_function, 
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
        self.N_ins = N_ins
        self.N_outs = N_outs
        self.inlets = inlets
        self.outlets = outlets
        self.boiler = boiler
        self.wastewater = wastewater
        self.ignored_HXN = ignored_HXN
        self.flowsheet = None
        self.system = None
        
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
