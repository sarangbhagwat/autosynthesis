# -*- coding: utf-8 -*-
"""
Created on Wed Sep  3 20:40:26 2025

@author: sarangbhagwat
"""

import numpy as np
import biosteam as bst
import thermosteam as tmo

__all__ = ('get_all_possible_distillation_trains', 
           'get_distillation_superstructure', 
           'TargetProduct', 'TargetProductsSet')

#%%
FakeSplitter = bst.units.FakeSplitter
System = bst.System

azeotrope_infeasible_recovery_identifier = 'cannot meet specifications'

#%% 
class TargetProduct():
    def __init__(self, ID, criteria):
        self.ID = ID
        self.criteria = criteria
    
    def test_criteria(self, stream):
        criteria = self.criteria
        return [criterion(stream) for criterion in criteria]
    
    def passes_all_criteria(self, stream):
        test_criteria_results = self.test_criteria(stream)
        for i in test_criteria_results:
            if not i: return False
        return True
    
    def add_criterion(self, criterion):
        self.criteria.append(criterion)


class TargetProductsSet():
    def __init__(self, ID, target_products, holistic_criteria):
        self.ID = ID
        self.target_products = target_products
        self.holistic_criteria = holistic_criteria
    
    def test_holistic_criteria(self, streams):
        h_criteria = self.holistic_criteria
        return [h_criterion(streams) for h_criterion in h_criteria]
    
    def passes_all_holistic_criteria(self, streams):
        test_h_criteria_results = self.test_holistic_criteria(streams)
        for i in test_h_criteria_results:
            if not i: return False
        return True
    
    def passes_all_individual_criteria(self, streams):
        tps = self.target_products
        passed = [False for tp in range(len(tps))]
        for stream in streams:
            for i, tp in zip(range(len(tps)), tps):
                if tp.passes_all_criteria(stream):
                    passed[i] = True
        for p in passed:
            if not p:
                return False
        return True
    
    def passes_all_criteria(self, streams):
        if self.passes_all_holistic_criteria(streams) and self.passes_all_individual_criteria(streams):
            return True
        else:
            return False
        
    def add_criterion(self, criterion):
        self.criteria.append(criterion)



#%%
class DistillationSuperstructure():
    def __init__(self, ID, system, splitters, columns):
        self.ID = ID
        self.system = system
        self.splitters = splitters
        self.columns = columns
    
    def is_a_terminal_unit(self, unit):
        for i in unit.outs:
            if i.sink is not None:
                return False
        return True
    
    @property
    def terminal_columns(self):
        cols = self.columns
        is_a_terminal_unit = self.is_a_terminal_unit
        return [col for col in cols if is_a_terminal_unit(col)]


#%%
def get_distillation_superstructure(stream, 
                           # distillation_type='Fenske-Underwood-Gilliland', 
                           distillation_type='McCabe-Thiele', 
                           chems_sorted=None, 
                           threshold_molfrac=1e-3,
                           threshold_mol=5.,
                           max_i=20,
                           distillation_kwargs={},
                           mixer_kwargs={}):
 
    dist_kwargs = {'k': 1.2, 
                   'P': 101325.0,
                   'vessel_material': 'Stainless steel 316',
                   'partial_condenser': False,
                   }
    dist_kwargs.update(distillation_kwargs)
    
    streams = [stream]
    all_splitters, all_columns = [], []
    i = 0
    
    while (not streams==[]) and (i<max_i):
        print(f'\n\n\n{i}')
        # for s1 in streams: stream.show()
        
        s = streams.pop()
        LHKs = get_possible_LHKs(stream=s, threshold_molfrac=threshold_molfrac, threshold_mol=threshold_mol)
        layer_splitter, layer_columns = None, None
        if not LHKs==[]:
            layer_splitter, layer_columns = get_distillation_network_layer(stream=s, 
                                                       distillation_type=distillation_type,
                                                       LHKs=LHKs, i=i,
                                                       dist_kwargs=dist_kwargs,
                                                       mixer_kwargs=mixer_kwargs)
        
            for D in layer_columns:
                streams += list(D.outs)
            
            if layer_splitter is not None: 
                all_splitters += [layer_splitter]
            
            all_columns += layer_columns
        
            i += 1
        
    # reconnect_to_columns_only(all_splitters, all_columns)
    
    sys = System.from_units(f'distillation_superstructure_{stream.ID}', units=all_columns+all_splitters)
    
    return DistillationSuperstructure(ID=f'ss_{stream.ID}', system=sys, splitters=all_splitters, columns=all_columns)


#%%
def get_possible_LHKs(stream, threshold_molfrac, threshold_mol):
    chems_sorted = sorted([c for c in stream.chemicals 
                           if stream.imol[c.ID]>threshold_mol
                           and stream.imol[c.ID]/stream.F_mol>threshold_molfrac], 
                          key=lambda c: c.Tb)
    chems = chems_sorted
    # stream.show()
    # print([c.ID for c in chems])
    LHKs = [(chems[j].ID, chems[j+1].ID) for j in range(len(chems)-1)]
    
    # print(LHKs)
    return LHKs

#%%
def optimize_column_recoveries(column, bounds=(0.001, 0.999), steps=5):
    col = column
    Lrs = np.linspace(bounds[0], bounds[1], steps)
    Hrs = np.linspace(bounds[0], bounds[1], steps)
    
    feasible_recs = []
    best_recs = (0.0, 0.0)
    for Lr in Lrs:
        for Hr in Hrs:
            try:
                col.Lr, col.Hr = Lr, Hr
                col.simulate()
                feasible_recs.append((Lr, Hr))
                if Lr*Hr > best_recs[0]*best_recs[1]:
                    best_recs = (Lr, Hr)
                    
            except Exception as e:
                if azeotrope_infeasible_recovery_identifier in str(e)\
                   or 'divide by zero' in str(e)\
                   or 'failed to find bracket' in str(e)\
                   or 'invalid value encountered' in str(e)\
                   or 'significant intermediate volatile' in str(e):
                    pass
                else:
                    raise e
    
    col.Lr, col.Hr = best_recs
    
    return best_recs


#%%
def get_distillation_network_layer(stream, distillation_type, LHKs, i, dist_kwargs, mixer_kwargs):
    layer_columns = []
    Distillation = None
    if distillation_type in ('McCabe-Thiele', 'Binary'):
        Distillation = bst.units.BinaryDistillation
    elif distillation_type in ('Shortcut', 'Fenske-Underwood-Gilliland', 'FUG'):
        Distillation = bst.units.ShortcutColumn
    else:
        raise ValueError(f'distillation_type {distillation_type} not supported.')
        
    S = FakeSplitter(f'S{i}', ins=stream, outs=('' for j in range(len(LHKs))), **mixer_kwargs)
    @S.add_specification(run=False)
    def copy_to_outs():
        feed = S.ins[0]
        for eff in S.outs: eff.copy_like(feed)
    
    S.simulate()
    
    j = 0
    for eff, LHK in zip(S.outs, LHKs):
        # print(LHK)
        D = Distillation(f'D{i}_{j}', ins=eff, LHK=LHK, Lr=0.99, Hr=0.99, **dist_kwargs)
        # try:
        optimize_column_recoveries(D)
        if not D.Lr==D.Hr==0.0: 
            D.simulate()
            layer_columns.append(D)
        # except Exception as e:
            # if azeotrope_infeasible_recovery_identifier in str(e).lower():
            #     print(f'\n\nThe below stream forms an azeotrope that cannot be split with recoveries {D.Lr, D.Hr} for keys {LHK}:\n')
                # eff.show(N=100)
            # else:
            # raise e
        j += 1
    
    return S, layer_columns


#%%
def reconnect_to_columns_only(splitters, columns):
    for S in splitters:
        S_reconnected = False
        for D in columns:
            for so in S.outs:
                if so.sink==D: # check if S feeds D
                    # reconnect
                    S.ins[0]-0-D
                    S_reconnected = True
                    break
            if S_reconnected:
                break


#%%
def get_all_possible_distillation_trains(distillation_superstructure, target_products_set=None):
    # cols = distillation_superstructure.terminal_columns
    cols = distillation_superstructure.columns
    dss = distillation_superstructure
    reconnect_to_columns_only(dss.splitters, dss.columns)
    trains_units = []
    for col in cols:
        upstream_units = col.get_upstream_units()
        trains_units.append([col]+[i for i in upstream_units if i in distillation_superstructure.columns])
    
    trains = []
    i = 0
    for tu in trains_units:
        trains.append(bst.System.from_units(ID=f'train_{i}', units=tu))
        i += 1
    
    if target_products_set is None:
        return trains
    else:
        satisfactory_trains = []
        for train in trains:
            if target_products_set.passes_all_criteria(train.streams):
                satisfactory_trains.append(train)
        return satisfactory_trains

