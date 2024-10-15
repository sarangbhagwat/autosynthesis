# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2022-, Sarang Bhagwat <sarangb2@illinois.edu>
# 
# This module is under the UIUC open-source license. See 
# github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE.txt
# for license details.
"""
Created on Tue Oct 15 00:18:30 2024

@author: sarangbhagwat
"""
import networkx as nx
from matplotlib import pyplot as plt

from .feedstock_to_sugars import cane_juicing, corn_dry_grind, cellulosic_pretreatment_saccharification
from .sugar_fermentation import fermentation_HP, fermentation_TAL, fermentation_ethanol
from .product_separation import HP_solution_separation, TAL_separation, ethanol_separation
from .product_upgrading import HP_solution_upgrading_acrylic_acid, TAL_upgrading_potassium_sorbate

__all__ = ('BlockSuperstructure',)

_all_process_blocks = [
    
    # feedstock_to_sugars
    cane_juicing.SugarcaneJuicing(),
    corn_dry_grind.CornDryGrind(),
    cellulosic_pretreatment_saccharification.CellulosicPretreatmentSaccharification(),
    
    # sugar_fermentation
    fermentation_HP.FermentationHP(),
    fermentation_TAL.FermentationTAL(),
    fermentation_ethanol.FermentationEthanol(),
    
    # product_separation
    HP_solution_separation.HPSolutionSeparation(),
    TAL_separation.TALSeparation(),
    ethanol_separation.EthanolSeparation(),
    
    # product_upgrading
    HP_solution_upgrading_acrylic_acid.HPSolutionUpgradingAcrylicAcid(),
    TAL_upgrading_potassium_sorbate.TALUpgradingIPAPotassiumSorbate(),
    TAL_upgrading_potassium_sorbate.TALUpgradingTHFEthanolPotassiumSorbate(),
    ]

_all_exclusively_feedstocks = [
    'corn',
    'sugarcane',
    'sweet sorghum',
    'corn stover',
    'miscanthus',
    'switchgrass',
    'wheat straw',
    ]

_all_exclusively_products = [
    'glacial acrylic acid',
    'ethanol',
    'potassium sorbate',
    ]

class BlockSuperstructure():
    
    def __init__(self, ID='DefaultBlockSuperstructure', 
                 process_blocks=_all_process_blocks,
                 exclusively_feedstocks=_all_exclusively_feedstocks,
                 exclusively_products=_all_exclusively_products,
                 ):
        self.ID = ID
        self.process_blocks = {i.ID: i for i in process_blocks} if isinstance(process_blocks, list) else process_blocks
        self._graph = None
        self.exclusively_feedstocks = _all_exclusively_feedstocks
        self.exclusively_products = _all_exclusively_products
    
    @property
    def graph(self): return self._graph
    
    def create_graph(self):
        G = nx.DiGraph()
        process_blocks = self.process_blocks
        # process_blocks_keys = process_blocks.keys()
        # nodes = [i.ID for i in process_blocks_keys]
        process_blocks_items = process_blocks.items()
        
        for ki, vi in process_blocks_items:
            for kj, vj in process_blocks_items:
                if not ki==kj:
                    for ei in vi._out_edges:
                        for ej in vj._acceptable_in_edges:
                            if ei==ej: G.add_edge(ki, kj, name=ei)
        
        for feed in self.exclusively_feedstocks:
            for ki, vi in process_blocks_items:
                for ei in vi._acceptable_in_edges:
                    if feed==ei: G.add_edge(feed, ki, name=ei)
        
        for prod in self.exclusively_products:
            for ki, vi in process_blocks_items:
                for ei in vi._out_edges:
                    if prod==ei: G.add_edge(ki, prod, name=ei)
                    
        self._graph = G
        
        return G
    
    def draw_graph(self, draw_edge_labels=False):
        G = self._graph
        pos = nx.spring_layout(G, k=1., iterations=100)
        plt.figure()
        nx.draw(
            G, pos, edge_color='black', width=1, linewidths=1,
            node_size=500, node_color='pink', alpha=0.9,
            labels={node: node for node in G.nodes()}
        )
        if draw_edge_labels:
            nx.draw_networkx_edge_labels(
                G, pos,
                edge_labels=nx.get_edge_attributes(G, 'name', default=''),
                font_color='blue'
            )
        plt.axis('off')
        plt.show()
    
    def get_all_paths(self, A, B):
        return list(nx.all_simple_paths(self._graph, A, B))
    
    def get_and_draw_all_paths(self, A, B):
        all_paths = self.get_all_paths(A, B)
        G = nx.DiGraph()
        for p in paths:
            for i in range(len(p-1)):
                G.add_edge(p[i], p[i+1])
        G = self._graph
        pos = nx.spring_layout(G, k=1., iterations=100)
        plt.figure()
        nx.draw(
            G, pos, edge_color='black', width=1, linewidths=1,
            node_size=500, node_color='pink', alpha=0.9,
            labels={node: node for node in G.nodes()}
        )
        plt.axis('off')
        plt.show()
        
        