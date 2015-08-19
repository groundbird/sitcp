#!/usr/bin/env python
# -*- coding: utf-8 -*-

from slowCtrl import RBCP, RBCPError
from readout import iq_read, iq_data_read, hexdump
from time import sleep
import numpy as np

def rms(x, axis=None):
    if not isinstance(x, np.ndarray):
        x = np.array(x)
    return np.sqrt(np.mean(x*x, axis=axis))

def sweep(fmin=-1e8, fmax=1e8, fres=1e6, p=100):
    fran = np.arange(fmin, fmax+fres, fres)
    s = RBCP()
    f1 = open('data/swp.dat', 'w')
    for _f in fran:
        s.set_freq(_f)
        iq_read('data/swp_%s' % _f, p)
        ts, _i, _q = iq_data_read(hexdump('data/swp_%s' % _f))
        i_mean = np.mean(_i)
        q_mean = np.mean(_q)
#         i_rms  = rms(_i)
#         q_rms  = rms(_q)
#         i_std  = np.std(_i)
#         q_std  = np.std(_q)

#         z = np.array(_i) + np.array(_q)*1j
#         z = i_mean + 1j*q_mean
#         amp_std = np.std(np.abs(z))
#         pha_std = np.std(np.angle(z))
#         i_std2 = rms(_i - i_mean)
#         q_std2 = rms(_q - q_mean)
#         z = i_mean + 1j*q_mean
#         amp = np.abs(z)
#         pha = np.arctan(q_mean/i_mean)
        print >> f1, '%d  %f  %f' % (_f, i_mean, q_mean)
        print '%+.4e\t'*3         % (_f, i_mean, q_mean)
        f1.flush()

        f2 = open('data/iq_%s.dat' % _f, 'w')
        for i, q in zip(_i, _q):
            print >> f2, '%f\t'*2 % (i, q)
        f2.close()
        
    f1.close()
    print '-'*10
    print 'Succeeded in readout IQ-data'

if __name__ == '__main__':
    sweep(fres=1e5)
