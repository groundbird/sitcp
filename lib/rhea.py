#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

class SweepDataError(Exception):
    def __init_(self, msg):
        self.msg = 'SweepData Error: %s' % str(msg)
        
    def __str__(self):
        return self.msg
        
class SweepData(object):
    def __init__(self, freq, i, q, i_raw=None, q_raw=None):
        self.freq  = np.array(freq)
        self.i     = np.array(i)
        self.q     = np.array(q)
        self.i_raw = np.array(i_raw) if i_raw is not None else None
        self.q_raw = np.array(q_raw) if q_raw is not None else None
        if self.i_raw is not None:
            self.ch     = len(self.i_raw)
            self.sample = len(self.i_raw[0][0])
        
    def __getitem__(self, key):
        if not isinstance(key, slice):
            raise ValueError('SweepData.__getitem__ does not suppots it')
            
        if self.i_raw is None:
            return SweepData(self.freq[key], self.i[key], self.q[key])
        else:
            return SweepData(self.freq[key], self.i[key], self.q[key],
                            [self.i_raw[c][key] for c in range(self.ch)],
                            [self.q_raw[c][key] for c in range(self.ch)])
    
    def __len__(self):
        return len(self.freq)

    @property
    def amp(self):
        return np.abs(self.i + 1j* self.q)

    
def read_sweep(fname, nchan=2, skiprows=10, skipfooter=None, comment='#', delimiter=','):
    with open(fname, 'r') as f:
        lines = f.readlines()

    if skipfooter is not None:
        lines = lines[skiprows:-skipfooter]
    else:
        lines = lines[skiprows:]
        
    d_unit = len(lines[0].split(delimiter)) # this value is 3 if -r option is not set
    
    freq  = []
    i     = []
    q     = []
    i_raw = [list() for k in range(nchan)] if d_unit > 3 else None
    q_raw = [list() for k in range(nchan)] if d_unit > 3 else None
    for line in lines:
        if line[0] == comment: continue
        l = [float(x) for x in line.split(delimiter)]
        freq.append(l[0])
        i.append(l[1])
        q.append(l[2])
        if i_raw is None: continue
        sample = (len(l) - 3) / (nchan*2)
        for ch in range(nchan):
            i_raw[ch].append(l[       ch *sample+3 :       (ch+1)*sample+3])
            q_raw[ch].append(l[(nchan+ch)*sample+3 : (nchan+ch+1)*sample+3])

    if i_raw is None:
        return SweepData(freq, i, q)
    else:
        return SweepData(freq, i, q, i_raw, q_raw)
