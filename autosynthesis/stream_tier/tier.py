# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2020-, Sarang Bhagwat <sarangb2@illinois.edu>
# 
# This module is under the UIUC open-source license. See 
# github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE.txt
# for license details.
"""
Created on Sat Apr 2 21:25:33 2022

@author: sarangbhagwat
"""
#%% Imports and setup
import thermosteam as tmo
import biosteam as bst
from thermosteam import Stream
import numpy as np

__all__ = ('StreamTier')

#%%
class StreamTier():
    
    def __init__(self, name, criteria):
        self.name = name
        self._criteria = criteria
    
    @property
    def criteria(self):
        return self._criteria
    
    def test_criteria(self, stream):
        criteria = self.criteria
        return np.all([criterion(stream) for criterion in criteria])

#%%
class TierTop(StreamTier):
    
    def __init(self, name, units):
        self._units = units
        StreamTier.__init__(self, name=name, criteria=self._get_all_units_criteria(units))
        
    def _get_all_units_criteria(self, units):
        criteria = []
        for unit in units:
            criteria += unit.feed_criteria
        return criteria
    
    @property
    def units(self):
        return self._units
    
    @property
    def criteria(self):
        return self._get_all_units_criteria(self.units)


#%%
class TierMid(StreamTier):
    # all TierMid thresholds are lower thresholds, >.
    # upper thresholds are not checked except for TierBottom, 
    # so ensure stream tiers are tested from top to bottom.
    def __init__(self, 
               name, 
               useful_chem_IDs, 
               total_threshold, # float; % as decimal
               individual_thresholds={}, # format: {String chem_ID: (float threshold, String kind)} OR {List or tuple of String chem_IDs: (float threshold, String kind)}
               total_threshold_kind='mass', # composition only; i.e., mass=>mass%, mol=>mol%, vol=>vol%
               ):
        
        self._individual_thresholds = individual_thresholds
        self._total_threshold = total_threshold
        self._total_threshold_kind = total_threshold_kind
        self._useful_chem_IDs = useful_chem_IDs
        
        StreamTier.__init__(self, 
                            name=name,
                            criteria=self._get_all_chems_criteria(useful_chem_IDs, 
                                                                  total_threshold,
                                                                  total_threshold_kind, 
                                                                  individual_thresholds))
        
    def _get_all_chems_criteria(self, useful_chem_IDs, total_threshold, total_threshold_kind, individual_thresholds):
        criteria = []
        criteria.append(lambda stream: 
                        stream.__getattribute__('i'+total_threshold_kind)[useful_chem_IDs].sum()
                        /stream.__getattribute__('F_'+total_threshold_kind)
                        > total_threshold)

        for chem_ID, (threshold, kind) in individual_thresholds.items():
            criteria.append(lambda stream: 
                            stream.__getattribute__('i'+kind)[chem_ID].sum()
                            /stream.__getattribute__('F_'+kind)
                            > threshold)
        return criteria
    
    @property
    def criteria(self):
        return self._get_all_chems_criteria(self._useful_chem_IDs, self._total_threshold, self._total_threshold_kind, self._individual_thresholds)

#%% 
class TierBottom(StreamTier):
    # individual TierBottom thresholds are upper thresholds, <=.
    def __init__(self, 
               name, 
               useful_chem_IDs, 
               total_threshold_upper, # float; % as decimal
               total_threshold_lower=0., # float; % as decimal
               individual_thresholds={}, # format: {String chem_ID: (float threshold, String kind)} OR {List or tuple of String chem_IDs: (float threshold, String kind)}
               total_threshold_kind='mass', # composition only; i.e., mass=>mass%, mol=>mol%, vol=>vol%
               ):
        
        self._individual_thresholds = individual_thresholds
        self._total_threshold_upper = total_threshold_upper
        self._total_threshold_lower = total_threshold_lower
        self._total_threshold_kind = total_threshold_kind
        self._useful_chem_IDs = useful_chem_IDs
        
        StreamTier.__init__(self, 
                            name=name,
                            criteria=self._get_all_chems_criteria(useful_chem_IDs, 
                                                                  total_threshold_upper,
                                                                  total_threshold_lower,
                                                                  total_threshold_kind, 
                                                                  individual_thresholds))
        
    def _get_all_chems_criteria(self, useful_chem_IDs, total_threshold_upper, total_threshold_lower, 
                                total_threshold_kind, individual_thresholds):
        criteria = []
        criteria.append(lambda stream: 
                        stream.__getattribute__('i'+total_threshold_kind)[useful_chem_IDs].sum()
                        /stream.__getattribute__('F_'+total_threshold_kind)
                        <= total_threshold_upper)
        criteria.append(lambda stream: 
                        stream.__getattribute__('i'+total_threshold_kind)[useful_chem_IDs].sum()
                        /stream.__getattribute__('F_'+total_threshold_kind)
                        > total_threshold_lower)
            
        for chem_ID, (threshold, kind) in individual_thresholds.items():
            criteria.append(lambda stream: 
                            stream.__getattribute__('i'+kind)[chem_ID].sum()
                            /stream.__getattribute__('F_'+kind)
                            <= threshold)
        return criteria
    
    @property
    def criteria(self):
        return self._get_all_chems_criteria(self._useful_chem_IDs, 
                                            self._total_threshold_upper, self._total_threshold_lower,
                                            self._total_threshold_kind, self._individual_thresholds)
