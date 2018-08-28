#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 14 11:35:46 2018

@author: maciejdragan
"""

import pandas as pd
import numpy as np
import os as os


class FuturesData():
    """ sources and houses futures data for downstream queries """
    
    def __init__(self, fldr_meta='/Users/maciejdragan/Documents/ProjectPluto/Data/', \
                       fldr_futures='/Users/maciejdragan/Documents/ProjectPluto/Repository/research/FuturesData2CSV/data/'):
        """ initialize FuturesData class """
        self.meta = pd.read_csv(fldr_meta + 'Futures/_meta_roots.csv', index_col=0)
        
        all_files = os.listdir(fldr_futures)        
        self.settle = pd.concat( [pd.read_csv(fldr_futures+f, index_col=0) for f in all_files],
                                  axis=1,
                                  keys=[f.split('.')[0] for f in all_files])
        self.settle.columns.names = ('tckr','fld')
        self.settle.index = pd.to_datetime(self.settle.index)
        
        self.settle = self.add_calculated_fields(self.settle)
        
    def add_calculated_fields(self, df):
        def add_rtn_index(df, fut_mults):          
            df_ridx     = df.xs('px_settle', level='fld', axis=1) + df.xs('adjAdd',  level='fld', axis=1)
            df_ridx_pct = df.xs('px_settle', level='fld', axis=1) * df.xs('adjMult', level='fld', axis=1)
            
            df_ridx = df_ridx*fut_mults
            
            df_rtn = pd.concat([df_ridx,df_ridx_pct],axis=1,keys=['ridx','ridx_pct']).swaplevel(axis=1)
            df_rtn.columns.names = ('tckr','fld')
            
            return pd.concat([df, df_rtn], axis=1).sort_index(axis=1)

        def add_contract_value(df):
            fut_mult = self.meta.Big_Point_Value.copy()
            fut_mult[ np.isnan(fut_mult) ] = 1
            fut_mult.index = [tckr+'1' for tckr in list(fut_mult.index)]
            
            df_ = df.xs('px_settle', level='fld', axis=1)
            df_contract_value = df_*fut_mult[df_.columns]
            df_contract_value.columns = pd.MultiIndex.from_product([df_contract_value.columns, ['contract_value']])
            df_contract_value.swaplevel(axis=1)
            df_contract_value.columns.names = ('tckr','fld')
            
            return pd.concat([df, df_contract_value], axis=1).sort_index(axis=1)
            
        df = add_rtn_index(df, self.get_fut_mults())
        df = add_contract_value(df)
        return df
        
    def __repr__(self):
        return ('Futures Data Class with Assets: \n' + 
                str(self.get_tckr_list()))
        
    def get_fut_mults(self):
        fut_mult = self.meta.Big_Point_Value.copy()
        fut_mult[ np.isnan(fut_mult) ] = 1
        fut_mult.index = [tckr+'1' for tckr in list(fut_mult.index)] 
        return fut_mult
        
        
    def get_tckr_list(self):
        """ returns list of tickers in settlement data """
        return list(self.settle.columns.get_level_values('tckr').unique())
    
    def get_field_list(self):
        """ returns list of tickers in settlement data """
        return list(self.settle.columns.get_level_values('fld').unique())
   
    
    def get_date_range(self):
        return self.settle.index
    '''
    def get_available_fields(self, tckrs=''):           
        all_static_fields   = list(fd.settle.columns.get_level_values('fld').unique())           
        all_calc_fields     = ['ridx','ridx_notl']
        
        return ({'static': set(all_static_fields), 
                   'calc': set(all_calc_fields)})
    '''
        
    def get_ts_data(self, field_names, date_time=None, tckrs=''):
        """ returns a dataframe of field values for tickers & dates """
        if tckrs=='':
            tckrs = self.get_tckr_list()
            
        if date_time is None:
            date_time = self.get_date_range()
        else:
            date_time = pd.DatetimeIndex(date_time)
            
        ts_data = self.settle.loc[date_time,(tckrs,field_names)]
        return ts_data.copy()
    
    
    def get_static_field(self, field_name, date_time, tckrs):
        ts_data = pd.DataFrame(index=date_time, columns=tckrs)
        for tckr in ts_data:
            ts_data[tckr] = self.settle[tckr][field_name]
            
        return ts_data


