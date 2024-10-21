# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 15:12:56 2024

@author: sarangbhagwat
"""

__all__ = ('feedstocks', 'products', 
           'model_static_queries', 'model_static_changes', 
           'model_dynamic_queries', 'model_dynamic_changes')


feedstocks = [
    'dextrose monohydrate',
    'corn',
    'sugarcane',
    'sweet sorghum',
    'corn stover',
    'miscanthus',
    'switchgrass',
    'wheat straw',
    ]

products = [
    'glacial acrylic acid', 'acrylic acid',
    'potassium sorbate', 'sorbic acid',
    'sodium 3-hydroxypropionate', '3-HP salt'
    'lactic acid', 'lactate',
    'succinic acid', 'succinate',
    'ethanol',
    ]

model_static_queries = [ # queries common to any system, or for which the dynamic aspect can be handled in AutoSynthesis
    # TEA
    'minimum product selling price',
    'installed cost',
    'total capital cost',
    'breakdown of capital cost contributions',
    'annual operating cost',
    'breakdown of annual operating cost contributions',
    'breakdown of utility demands',
    'variable operating cost',
    'fixed operating cost',
    'electric power consumption',
    'electric power production'
    'TEA year',
    'prices',
    # LCA
    'carbon intensity',
    'breakdown of carbon intensity contributions',
    'fossil energy consumption',
    'breakdown of fossil energy consumption contributions',
    'impact characterization factors'
    ]

model_static_changes = [
    'fermentation yield (g/g)',
    'fermentation titer (g/L)',
    'fermentation productivity (g/L/h)',
    'fermentation co-product yields',
    'feedstock capacity',
    'production capacity',
    ]

model_dynamic_queries = [
    # unit-specific results
    # raw material-specific results
    ]

model_dynamic_changes = [
    # unit-specific design parameters
    'prices',
    'impact characterization factors',
    ]

