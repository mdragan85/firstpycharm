#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 09:41:18 2018

@author: maciejdragan
"""
import tigon as tgn
import matplotlib.pyplot as plt

def build_risk_parity():
    weq  = tgn.Weights.from_constant_vol(fd, ['z1', 'es1'])
    wfi  = tgn.Weights.from_constant_vol(fd, ['ty1', 'rx1'])
    wcom = tgn.Weights.from_constant_vol(fd, ['cl1', 'ho1', 'gc1'])

    return (weq.volnorm() + wfi.volnorm() + wcom.volnorm() * 0.50).volnorm()


fd = tgn.FuturesData()

mdlrp = build_risk_parity()
mdlrp.cumpnl()[-5000:].plot()
print(mdlrp.sharpe())

plt.show()
