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
from compiler.ast import flatten

__version__ = '0.0.1'

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
g.add_argument(
    # IQ data output
    '-r',
    '--raw',
    action  = 'store_true',
    dest    = 'raw',
    help    = 'Save raw IQ data. The deault value is False.')
args = p.parse_args()

date   = datetime.utcnow()
fname  = 'data/sweep_%s.csv' % date.strftime('%Y%m%d_%H%M%S')
fran   = np.arange(args.fran[0], args.fran[1]+args.step, args.step)
sample = int(args.time*(SAMPLE_RATE/DOWNSAMPLE_RATE))
dsize  = int(sample*DATA_UNIT) # KB

# Generate object and connection
s = RBCP()
r = Readout()
r.connect()

# Begin the readout sequence
s.wr_adc()             # Reset ADC register
s.wr_dac()             # Reset DAC register
s.register_init        # Initialize ADC/DAC register
RHEA_temp = s.dac_temp # Get DAC temperature in degrees of Celsius

print """
Start frequency sweep readout.
--------------------------------------------------
Date                   : %s UTC
Frequency range        : %.2e to %.2e Hz
Frequency steps        : %.2e Hz
Observation time       : %s sec
# of channels          : %d
# of samples           : %d
Raw IQ data output     : %s
RHEA board temperature : %d deg C
--------------------------------------------------
Frequency [Hz]\tI\t\tQ
""" % (date.strftime('%Y-%m-%d %H:%M:%S'), args.fran[0], args.fran[1],
       args.step, args.time, N_CHANNEL, sample, args.raw, RHEA_temp)

with open(fname, 'w') as f:
    # CSV file header
    print >> f, """# Frequency sweep data (Ver. %s)
# Date                    : %s UTC
# Sampling rate           : %d Hz
# Frequency range         : %d to %d Hz
# Frequency steps         : %d Hz
# # of channels           : %d
# # of sample / frequency : %d
# Raw IQ data output      : %s
# RHEA board temperature  : %d deg C
""" % (__version__, date.strftime('%Y-%m-%d %H:%M:%S'),
       SAMPLE_RATE/DOWNSAMPLE_RATE, args.fran[0], args.fran[1], args.step,
       N_CHANNEL, sample, args.raw, RHEA_temp)

    for freq in fran:
        try:
#             s.set_freq(freq)
            s.set_freq(freq,   0, 0, False)
            s.set_freq(freq, 180, 1)
            r.clear()
            s.iq_tgl
            sleep(args.time + args.time*0.5)
            ts, i, q = fixed(r, dsize)
            i_mean = np.mean(i)
            q_mean = np.mean(q)

            print '%+e\t%+e\t%+e' % (freq, i_mean, q_mean) # debug
            if args.raw:
                lst = flatten([freq, i_mean, q_mean, i, q])
                print >>f, ('%d,%f,%f,'+'%f,'*(sample*2*N_CHANNEL-1)+'%f') % tuple(lst)
            else:
                print >>f, '%d,%f,%f' % (freq, i_mean, q_mean)
            f.flush()
            s.iq_tgl

        except RBCPError as e:
            if e.msg == 'RBCP Error: Write failed':
                print 'Retry'
                s.sitcp_reset
                sleep(10)
            else:
                print e.msg
                s.sitcp_reset
                exit()
            if s.chk_stat[1][0] == '0x1':
                s.iq_tgl;
            continue

        except KeyboardInterrupt:
            if s.chk_stat[1][0] == '0x1':
                s.iq_tgl; print '\nInterrupt off'
            r.close()
            exit()

    else:
        r.close()

print """
Finish frequency sweep readout.
Bye-Bye (^_^)/~
"""
