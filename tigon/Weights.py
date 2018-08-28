#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 10:10:39 2018

@author: maciejdragan
"""


from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os as os
import re as re

class Weights():
    """ Class representing security/asset weights """
    
    ANN_FCTR = np.sqrt(262)
    
    def __init__(self, df_weights , data_source=None):
        self.wgt = df_weights
        self.data_source = data_source
    
    @classmethod
    def from_constant_notional(cls, data_source, tckrs, notl=1e6):
        n_contracts = (notl/data_source.get_ts_data('contract_value',tckrs=tckrs))
        n_contracts.columns = n_contracts.columns.droplevel('fld')
        return cls(df_weights=n_contracts, data_source=data_source )
    
    @classmethod
    def from_constant_vol(cls, data_source, tckrs, target_vol=0.10):
        w = cls.from_constant_notional(data_source, tckrs)
        return w.volnorma()
    
    def __repr__(self):
        return self.wgt.__repr__()
    
    def __do_operation(self,other,operation):
        def operate_df_series(df,ser,operation):
            if   operation == '+':
                return df.add(ser,axis=0)
            elif operation == '-':
                return df.sub(ser,axis=0)
            elif operation == '*':
                return df.mul(ser,axis=0)
            elif operation == '/':
                return df.div(ser,axis=0).replace([np.inf, -np.inf], np.nan)
            else:
                raise TypeError('Operaton Not Supported!') 
                
        def operate_df_df(df,dfother,operation):
            if   operation == '+':
                return df+df_other
            elif operation == '-':
                return df-df_other
            elif operation == '*':
                return df*df_other
            elif operation == '/':
                return (df/df_other).replace([np.inf, -np.inf], np.nan)
            else:
                raise TypeError('Operaton Not Supported!')
        
        def operate_df_float(df,num,operation):
            if   operation == '+':
                return df+num
            elif operation == '-':
                return df-num
            elif operation == '*':
                return df*num
            elif operation == '/':
                return (df/num).replace([np.inf, -np.inf], np.nan)
            else:
                raise TypeError('Operaton Not Supported!')
        
        if isinstance(other, self.__class__):
            df_me, df_other = self._common_axis(self.wgt, other.wgt) 
            df_new = operate_df_df(df_me,df_other,operation)
        elif isinstance(other, pd.DataFrame):
            df_me, df_other = self._common_axis(self.wgt, other) 
            df_new = operate_df_df(df_me,df_other,operation)
        elif isinstance(other, pd.Series):
            df_me, ser_other = self._common_axis(self.wgt, other)
            df_new = operate_df_series(df_me, ser_other, operation)
        elif isinstance(other, (int,float)):
            df_new = operate_df_float(self.wgt, other, operation)
            
        return Weights(df_weights=df_new, data_source=self.data_source)
            
    def __add__(self, other):       
        return self.__do_operation(other,'+')
    def __sub__(self, other):       
        return self.__do_operation(other,'-')
    def __mul__(self, other):       
        return self.__do_operation(other,'*')
    def __truediv__(self, other): 
        return self.__do_operation(other,'/')


    def _common_axis(self, df_me, other):
        def commom_dts(df_me, other):
            return pd.DatetimeIndex.union(df_me.index,other.index)
        def common_cols(df_me, df_other):
            return df_me.columns.union(df_other.columns)
            
        # Reindex on time
        dt = commom_dts(df_me, other)
        df_me_ = df_me.reindex(index=dt).fillna(method='ffill')
        other_ = other.reindex(index=dt).fillna(method='ffill')
        
        # if other is Dataframe, reindex columns
        if isinstance(other_, pd.DataFrame):
            cols = common_cols(df_me_, other_)
            df_me_ = df_me_.reindex(columns=cols)
            other_ = other_.reindex(columns=cols)
        
        # return values and fill in 0 for NaN
        return df_me_.fillna(0), other_.fillna(0)
            
    def pnla(self):
        def get_dt_range():
            if isinstance(self.wgt.index.freq, pd.tseries.offsets.BusinessDay):
                return self.wgt.index
            else:
                return pd.date_range(self.wgt.index.min(),self.wgt.index.max(),freq='B')
            
        dtrng = get_dt_range()
        
        ridx = self.data_source.get_ts_data(['ridx'], date_time=dtrng, tckrs=list(self.wgt.columns)).bfill(axis=0)
        ridx.columns = ridx.columns.droplevel('fld')
        
        w = self.wgt.reindex(index=dtrng).ffill(axis=0)
        pnla = (ridx - ridx.shift())*(w.shift())
        
        return pnla

    def pnl(self):
        return self.pnla().sum(axis=1)
    
    def cumpnl(self):
        return self.pnl().cumsum()
    
    def sharpe(self):
        pnl = self.pnl()
        sr = pnl.mean() / pnl.std()
        return sr*np.sqrt(260)
    
    def rolling_sharpe(self,wnd=260):
        pnl = self.pnl()
        sr = pnl.rolling(wnd).mean() / pnl.rolling(260).std()
        return sr*np.sqrt(260)
    
    def volnorma(self, vol_target=0.10):
        vol1 = self.pnla().rolling(30).std()
        vol2 = self.pnla().rolling(60).std()
        vol  = pd.concat([vol1,vol2]).groupby(level=0).max()*self.ANN_FCTR
        
        return self / vol * vol_target
    
    def volnorm(self, vol_target=0.10):
        vol1 = self.pnl().rolling(30).std()
        vol2 = self.pnl().rolling(60).std()
        vol  = pd.concat([vol1,vol2]).groupby(level=0).max()*self.ANN_FCTR
        
        return self / vol * vol_target
    