# -*- coding: utf-8 -*-
"""
Created on Wed Nov  2 17:43:27 2022

@author: sarangbhagwat
"""
import biosteam as bst
import thermosteam as tmo
import flexsolve as flx
import numpy as np
import math


BatchCrystallizer = bst.BatchCrystallizer
IQ_interpolation = flx.IQ_interpolation
ln = math.log
exp = math.exp

class APDBatchCrystallizer(BatchCrystallizer):
    
    def __init__(self, ID='', ins=None, outs=(), 
                 target_recovery=0.6,
                 thermo=None,
                 tau=None, N=None, V=None, T=305.15,
                 Nmin=2, Nmax=36, vessel_material='Carbon steel',
                 kW=0.00746,
                 solute=None,
                 solvent=None,
                 get_solubility_given_T=None, # mol-solute/(mol-solute+mol-solvent)
                 T_range = (275.15, 371.15) # K # when a target recovery is specified, a T will be solved for within this range
                 ):
        
        BatchCrystallizer.__init__(self, ID, ins, outs, thermo,
                     tau, N, V, T,
                     Nmin, Nmax, vessel_material,
                     kW)
        self.solute = solute
        self.get_solubility_given_T = get_solubility_given_T
        self.target_recovery = target_recovery
        self.T_range = T_range
        self.effective_recovery = None
        self.tau = tau
        self.solvent = solvent
        
    def get_T_given_target_recovery(self, target_recovery):
        in_stream, = self.ins
        out_stream, = self.outs
        out_stream.copy_like(in_stream)
        solute = self.solute
        solvent = self.solvent
        T_range = self.T_range
        target_recovery = self.target_recovery
        get_solubility_given_T = self.get_solubility_given_T
        
        def obj_f_default(T):
            out_stream.sle(T=T, solute=solute)
            s_solute = out_stream.imol['s', solute]
            l_solute = out_stream.imol['l', solute]
            tot_solute = s_solute+l_solute
            return s_solute/tot_solute - target_recovery
        
        def obj_f_custom(T):
            tot_solute = in_stream.imol[solute]
            dissolved_solute = get_solubility_given_T(T) * in_stream.imol[solute, solvent].sum()
            return (1.-dissolved_solute/tot_solute) - target_recovery
        
        if get_solubility_given_T:
            obj_f = obj_f_custom
        else:
            obj_f = obj_f_default
            
        if obj_f(T_range[0]) < 0:
            T = T_range[0]
            self.effective_recovery = obj_f(T) + target_recovery
            return T
        try: 
            T = IQ_interpolation(obj_f, T_range[0], T_range[1])
            if T > in_stream.T:
                self.effective_recovery = obj_f(in_stream.T) + target_recovery
                return in_stream.T
            else:
                self.effective_recovery = obj_f(T) + target_recovery
        except Exception as e:
            raise e
        return T

    def _run(self):
        in_stream, = self.ins
        out_stream, = self.outs
        target_recovery = self.target_recovery
        
        out_stream.copy_like(in_stream)
        out_stream.phases=('l', 's')
        # self.effective_recovery = effective_recovery = target_recovery
        self.T = T = self.get_T_given_target_recovery(target_recovery)
        
