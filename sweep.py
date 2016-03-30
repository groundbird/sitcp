#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sys import argv, exit
from os import system
from os.path import getsize
from datetime import datetime
from struct import unpack
from time import sleep
from argparse import ArgumentParser
from compiler.ast import flatten

from lib.slowCtrl import *
from lib.readout import *
from fixed import *

__version__ = '0.0.1'

def chisquare(data, f_exp=np.mean):
    exp = f_exp(data)
    x = []
    for obs in data:
        y = (obs - exp)**2 / exp
        x.append(y)
    chisq = sum(x)
    return chisq

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
# g.add_argument(
#     # Saved filename
#     '-n',
#     '--name',
#     action  = 'store',
#     nargs   = '?',
#     default = 'data/sweep_%s.csv' % date.strftime('%Y%m%d_%H%M%S'),
#     type    = file,
#     dest    = 'name',
#     help    = 'Saved filename. The default value is sweep_<date>.')
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
""" % (date.strftime('%Y-%m-%d %H:%M:%S'), args.fran[0], args.fran[1],
       args.step, args.time, N_CHANNEL, sample, args.raw, RHEA_temp)
if args.raw:
    print 'f [Hz]\tI[i]\tQ[i]'
else:
    print 'f [Hz]\tI_mean[i]\tQ_mean[i]'

with open(fname, 'w') as f:
    # CSV file header
    print >>f, """# Frequency sweep data (Ver. %s)
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
#             s.set_freq(freq, 0, 0)
#             s.set_freq(freq)
            s.set_freq(freq, 0, 0, False)
            s.set_freq(freq, 0, 1)
            r.clear()
#             s.iq_tgl
#             sleep(args.time + args.time*0.5)
            s.iq_toggle('start')
            sleep(args.time*1.5*N_CHANNEL)
            ts, i, q = fixed(r, dsize)
#             i = zip(*[iter(i)]*N_CHANNEL)
#             q = zip(*[iter(q)]*N_CHANNEL)
            _i = np.array(i)
            _q = np.array(q)
            _i = _i.reshape(-1, N_CHANNEL)
            _q = _q.reshape(-1, N_CHANNEL)
            i_mean, q_mean, i_std, q_std = [], [], [], []
            for k in range(N_CHANNEL):
                i_mean.append(np.mean(_i[:,k]))
                q_mean.append(np.mean(_q[:,k]))
                i_std.append(np.std(_i[:,k]))
                q_std.append(np.std(_q[:,k]))
#             i_mean = np.mean(i)
#             q_mean = np.mean(q)
#             i_std  = np.std(i)
#             q_std  = np.std(q)
#             i_mean, q_mean, i_std, q_std = [], [], [], []
#             i_mean, q_mean = [], []
#             for j in range(N_CHANNEL):
#                 i_mean.append(np.mean(i[j]))
#                 q_mean.append(np.mean(q[j]))
#                 i_std.append(np.std(i[j]))
#                 q_std.append(np.std(q[j]))
            
#             i_chisq = chisquare(i)
#             q_chisq = chisquare(q)
#             print '%+e\t%+e\t%+e\t%+e\t%+e' % (freq, i_mean, q_mean,
#                                                i_std, q_std)
            i_mean = list(i_mean)
            q_mean = list(q_mean)
            i_std = list(i_std)
            q_std = list(q_std)
            arr = np.r_[freq, flatten(i_mean), flatten(q_mean),
                        flatten(i_std), flatten(q_std)]
#             arr = np.r_[freq, flatten(i_mean), flatten(q_mean)]
            form = '{:+.2e}'+'  {:+.2e}'*(arr.size-1)
            print form.format(*arr)

            if args.raw:
#                 lst = flatten([freq, i_mean, q_mean, i, q])
#                 print >>f, ('%d,%f,%f,'+'%f,'*(sample*2*N_CHANNEL-1)+'%f') % tuple(lst)
                arr_raw = np.r_[freq, i, q]
                form_raw = '{:.0f}'+',{:f}'*(arr_raw.size-1)
                print >>f, form_raw.format(*arr_raw)
            else:
#                 print >>f, '%d,%f,%f' % (freq, i_mean, q_mean)
                form = '{:.0f}'+',{:f}'*(arr.size-1)
                print >>f, form.format(*arr)

            f.flush()
#             s.iq_tgl
            s.iq_toggle('stop')

            # debug
#             if (i_std or q_std) > 10000:
#                 print '\nstandard deviation of I or Q > 10000'
#                 print 'f=%+e, I_std=%d, Q_std=%d' % (freq, i_std, q_std)
#                 exit()

        except RBCPError as e:
#             if e.msg == 'RBCP Error: Write failed':
#                 print 'Retry'
#                 s.sitcp_reset
#                 sleep(10)
#             else:
            print e.msg
            s.sitcp_reset
            exit()
#             if s.chk_stat[1][0] == '0x1':
#                 s.iq_tgl;
#             continue

        except KeyboardInterrupt:
#             if s.chk_stat[1][0] == '0x1':
            s.iq_toggle('stop')
            print ''
            r.close()
            exit()

    else:
        r.close()

print """
Finish frequency sweep readout.
Bye-Bye (^_^)/~
"""
