# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 15:12:56 2024

@author: sarangbhagwat
"""

__all__ = ('feedstocks', 'products', 
           'model_static_queries', 'model_static_changes', 
           'model_dynamic_queries', 'model_dynamic_changes')

#%% initial
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

#%% static interactions
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

#%% dynamic interactions
# note these will be dynamically generated for each new system; below items 
# are examples only


model_unit_name_examples = [
    'D401',
    'R302',
    'C601',
    'D301',
    'R301',
    'fermentation reactor',
    ]

model_unit_attribute_examples = [
    'material balance',
    'installed costs',
    'power utility',
    'heat utilities',
    'CO2 sparging rate',
    'all reactions',
    'glucose to 3-HP reaction',
    'glucose to acetic acid reaction',
    'light key recovery',
    'heavy key recovery',
    ]

model_stream_name_examples = [
    'feedstock',
    'acrylic acid',
    'sulfuric acid for reacidulation',
    'lime for neutralization',]

model_stream_attribute_examples = [
    'price',
    'cost',
    'mass flow',
    'molar flow',
    'volumetric flow',
    ]

model_dynamic_queries = []
import itertools
for i in itertools.product(model_unit_name_examples, model_unit_attribute_examples):
    model_dynamic_queries.append(i[0] + ' - ' + i[1])
for i in itertools.product(model_stream_name_examples, model_stream_attribute_examples):
    model_dynamic_queries.append(i[0] + ' - ' + i[1])

model_dynamic_changes = []
