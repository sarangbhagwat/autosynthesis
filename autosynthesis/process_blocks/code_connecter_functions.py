# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2022-, Sarang Bhagwat <sarang.bhagwat.git@gmail.com>
# 
# This module is under the UIUC open-source license. See 
# https://github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE
# for license details.
import autosynthesis

def create_biorefinery(feedstock, product, choice=None):
    sys = autosynthesis.process_blocks.get_system_block_based(feedstock=feedstock,
                                                        product=product,
                                                        choice=choice)
    return sys

def draw_plot(plot_type, sys, model):
    if plot_type=='process flowsheet':
        sys.diagram('cluster')
    elif plot_type in ('baseline TEA results', 'TEA results'):
        pass
    elif plot_type in ('baseline LCA results', 'LCA results'):
        pass

def get_attribute_or_parameter(attribute, sys, model=None):
    pass

def update_parameter(parameter, value, model=None):
    pass

def run_uncertainty_analysis(model):
    pass

def run_sensitivity_analysis(model):
    pass

