#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lib.slowCtrl import *
from lib.readout import *
from sys import argv, exit
from os import system
from os.path import getsize
from datetime import datetime
from struct import unpack
from time import sleep
from argparse import ArgumentParser
from fixed import *

# Command-line options
p = ArgumentParser(
    description = 'Take the frequency sweep readout data.')
g = p.add_argument_group()
g.add_argument(
    # Set frequency reange [Hz]
    '-f',
    '--freq',
    action  = 'store',
    nargs   = 2,
    default = [-1e8, 1e8], # Hz
    type    = float,
    dest    = 'fran',
    help    = 'The frequency range. The default values are -100e6/+100e6 (-100 MHz to 100 MHz).',
    metavar = ('[fmin]', '[fmax]'))
g.add_argument(
    # Set frequency step [Hz]
    '-s',
    '--step',
    action  = 'store',
    nargs   = '?',
    default = 1e6, # sec
    type    = float,
    dest    = 'step',
    help    = 'The frequency step. The default value is 1e6 (1 MHz).',
    metavar = 'step')
g.add_argument(
    # Set observation time [s]
    '-t',
    '--time',
    action  = 'store',
    nargs   = '?',
    default = 0.1, # sec
    type    = float,
    dest    = 'time',
    help    = 'The observation time per frequency. The default value is 0.1 (0.1 sec).',
    metavar = 's')
args = p.parse_args()

date   = datetime.today()
fname  = 'data/sweep_%s.dat' % date.strftime('%Y%m%d_%H%M%S')
fran   = np.arange(args.fran[0], args.fran[1]+args.step, args.step)
sample = args.time * (SAMPLE_RATE/DOWNSAMPLE_RATE)
dsize  = int(sample*DATA_UNIT) # KB

# Generate object and connection
s = RBCP()
r = Readout()
r.connect()

# Begin the readout sequence
j = 0 # readout on/off when j is odd/even
print """
Start frequency sweep readout.
--------------------------------------------------
Date             : %s
Frequency range  : %.2e to %.2e Hz
Frequency steps  : %.2e Hz
Observation time : %s sec
# of samples     : %d 
--------------------------------------------------
Frequency [Hz]\tI\t\tQ
""" % (date.strftime('%Y-%m-%d %H:%M:%S'),
       args.fran[0], args.fran[1], args.step, args.time, sample)

with open(fname, 'w') as f:
    for freq in fran:

        try:
            s.set_freq(freq)
            r.clear()
            s.iq_rd(); j+=1 # on
            sleep(0.1*dsize/1000) # depend on dsize
            ts, i, q = fixed(r, dsize)
            i_mean = np.mean(i)
            q_mean = np.mean(q)
            print >> f, '%+e\t%+e\t%+e' % (freq, i_mean, q_mean)
            f.flush()
            print '%+e\t%+e\t%+e' % (freq, i_mean, q_mean) # debug
            s.iq_rd(); j+=1 # off
        except KeyboardInterrupt:
            if j % 2: s.iq_rd() # off
            exit()

print """
Finish frequency sweep readout.
Bye-Bye (^_^)/~
"""
