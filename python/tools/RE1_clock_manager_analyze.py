#!/usr/bin/env python
from future.builtins import input
import time
import stretch_body.scope
import stretch_body.pimu
import stretch_body.wacc
import sys

import argparse
import stretch_body.hello_utils as hu
hu.print_stretch_re_use()

parser=argparse.ArgumentParser(description='Tool to analyze the Hardware Clock Manager')
parser.add_argument("--pimu", help="Analyze the Pimu Hardware Clock Manager",action="store_true")
parser.add_argument("--wacc", help="Analyze the Wacc Hardware Clock Manager",action="store_true")
parser.add_argument("--measure_kt", help="Measure difference in clock rates (Kt) between hardware and PC clock",action="store_true")
parser.add_argument("--measure_trs", help="Measure roundtrip time to status_sync the hw clock from the PC",action="store_true")
parser.add_argument("--measure_skew", help="Measure drift between calibrated clocks",action="store_true")
args=parser.parse_args()

if args.pimu:
    p=stretch_body.pimu.Pimu()
    p.startup()
elif args.wacc:
    p = stretch_body.wacc.Wacc()
    p.startup()
else:
    print('Specify Wacc or Pimu from command line...')
    exit()

if args.measure_skew:
    s = stretch_body.scope.Scope(num_points=500, yrange=[-5000, 5000], title='HW Clock Slower  than PC (usecs)')
    while(True):
        p.trigger_status_sync()
        p.clock_manager.pretty_print()
        s.step_display(p.clock_manager.adj_skew)
        p.pull_status()
        time.sleep(0.04)


if args.measure_kt:
    t0_pc=hu.SystemTimestamp().from_wall_time()
    p.trigger_status_sync()
    t0_hw=p.status['timestamp_status_sync']
    s=stretch_body.scope.Scope(num_points=100,yrange=[-2000,2000],title='Skew Rate KT (ppm)')
    print('Collecting 20 samples status sync of HW clock...')
    kt_ppm=0
    for i in range(2000):
        print('------------ '+str(i)+' -------------')
        tx_pc=hu.SystemTimestamp().from_wall_time()
        p.trigger_status_sync()
        tx_hw = p.status['timestamp_status_sync']
        dt_pc = tx_pc-t0_pc
        dt_hw = tx_hw-t0_hw
        e=(dt_pc-dt_hw).to_usecs()
        kt_ppm = e / dt_pc.to_secs()  # uSecs of drift per second

        print('DT PC',dt_pc)
        print('DT HW',dt_hw)
        print('PC clock faster than HW clock by (usecs)',e)
        print('Equivalent Kt (PPM): ',kt_ppm)

        s.step_display(kt_ppm)
        time.sleep(0.1)
    print('Done...')

if args.measure_trs:
    rt_log=[]
    print('Collecting 1000 samples roundtrip time to sync HW clock...')
    for i in range(1000):
        dt=p.clock_manager.sample_TRS()
        rt_log.append(dt)
    print('Done...')

    import matplotlib.pyplot as plt
    import numpy as np
    n, bins, patches = plt.hist(x=rt_log, bins='auto', color='#0504aa',alpha=0.7, rwidth=0.85)
    max_bin=bins[np.where(n == n.max())]
    print('Maximum bin (us): '+str(max_bin))
    plt.grid(axis='y', alpha=0.75)
    plt.xlabel('Time (us)')
    plt.ylabel('Occurances')
    plt.title('Clock Zero Roundtrip Time')
    plt.text(23, 45, r'$\mu=15, b=3$')
    maxfreq = n.max()
    plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)
    plt.show()
    print()
    d = input('Save TRS to YAML? [n]')
    if d == 'y' or d == 'Y':
        p.clock_manager.params['trs'] = float(max_bin)
        p.clock_manager.write_device_params(p.clock_manager.hw_device_name, p.clock_manager.params)

p.stop()
