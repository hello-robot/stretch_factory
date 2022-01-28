#!/usr/bin/env python
import os, sys
import math
import time
import stretch_body.robot
import stretch_body.scope
import sys
import random

import argparse
import stretch_body.hello_utils as hu
hu.print_stretch_re_use()

parser=argparse.ArgumentParser(description='Tool to analyze Stretch Timestamp Manager')
parser.add_argument("--sensor_stats", help="Measure stats of the sensor timestamps",action="store_true")
parser.add_argument("--runstop_toggle", help="Toggle runstop while measure",action="store_true")
parser.add_argument("--outlier_detect", help="Look for spurious values",action="store_true")
args=parser.parse_args()

r=stretch_body.robot.Robot()
r.startup()

if args.outlier_detect:
    print('Starting sensor timestamp analysis...')
    print('Sync mode enabled: ' + str(r.timestamp_manager.param['sync_mode_enabled']))
    print('Time align status: ' + str(r.timestamp_manager.param['time_align_status']))
    print('Use skew compensation: ' + str(r.pimu.clock_manager.params['use_skew_compensation']))
    print('---------------------------')
    while True:
        s = r.get_status()
        hw_sync = s['timestamps']['hw_sync']
        p0 = (s['timestamps']['pimu_imu'] - hw_sync).to_usecs()
        t0 = (s['timestamps']['left_wheel_enc'] - hw_sync).to_usecs()
        t1 = (s['timestamps']['right_wheel_enc'] - hw_sync).to_usecs()
        t2 = (s['timestamps']['lift_enc'] - hw_sync).to_usecs()
        t3 = (s['timestamps']['arm_enc'] - hw_sync).to_usecs()
        w0 = (s['timestamps']['wacc_acc'] - hw_sync).to_usecs()

if args.runstop_toggle:
    print('Starting sensor timestamp analysis...')
    print('Sync mode enabled: ' + str(r.timestamp_manager.param['sync_mode_enabled']))
    print('Time align status: ' + str(r.timestamp_manager.param['time_align_status']))
    print('Use skew compensation: ' + str(r.pimu.clock_manager.params['use_skew_compensation']))
    print('---------------------------')
    ts_hist = []
    nrs=20
    rs_on=nrs
    for i in range(100):
        s = r.get_status()
        hw_sync = s['timestamps']['hw_sync']
        t3 = (s['timestamps']['arm_enc'] - hw_sync).to_usecs()
        ts_hist.append(t3)
        if rs_on:
            if rs_on ==nrs:
                r.pimu.runstop_event_trigger()
                r.push_command()
                print('Runstop triggered...')
            rs_on=rs_on-1
        else:
            r.pimu.runstop_event_reset()
            r.push_command()
            print('Runstop reset...')
            rs_on=nrs

        time.sleep(random.random() * 0.1)
        print('I: '+str(i)+' T3: ', t3)
    r.stop()
    import matplotlib.pyplot as plt

    fig, axs = plt.subplots(1, 1, sharey=True, tight_layout=True)
    axs.hist(x=ts_hist, bins='auto', color='#0504aa', alpha=0.7, rwidth=0.85)
    axs.set_title('Arm Encoder')
    plt.show()

if args.sensor_stats:
  print('Starting sensor timestamp analysis...')
  print('Sync mode enabled: '+str(r.timestamp_manager.param['sync_mode_enabled']))
  print('Time align status: ' + str(r.timestamp_manager.param['time_align_status']))
  print('Use skew compensation: ' + str(r.pimu.clock_manager.params['use_skew_compensation']))
  print('---------------------------')
  ts_hist=[[],[],[],[],[], []]
  for i in range(1000):
      print('I '+str(i)+' of 1000')
      s=r.get_status()
      hw_sync=s['timestamps']['hw_sync']
      p0 = (s['timestamps']['pimu_imu']-hw_sync).to_usecs()
      t0=  (s['timestamps']['left_wheel_enc']-hw_sync).to_usecs()
      t1 = (s['timestamps']['right_wheel_enc'] - hw_sync).to_usecs()
      t2 = (s['timestamps']['lift_enc'] - hw_sync).to_usecs()
      t3 = (s['timestamps']['arm_enc'] - hw_sync).to_usecs()
      w0 = (s['timestamps']['wacc_acc'] - hw_sync).to_usecs()

      ts_hist[0].append(t0)
      ts_hist[1].append(t1)
      ts_hist[2].append(t2)
      ts_hist[3].append(t3)
      ts_hist[4].append(p0)
      ts_hist[5].append(w0)
      print(r.status['timestamps'])
      time.sleep(random.random()*0.1) #Randomize timing so get non biased distribution
  r.stop()
  import matplotlib.pyplot as plt
  import numpy as np
  fig, axs = plt.subplots(1, 6, sharey=True, tight_layout=True)
  fig.suptitle('Distribution of sensor timestamps from sync line event')

  axs[0].hist(x=ts_hist[0], bins='auto', color='#0504aa', alpha=0.7, rwidth=0.85)
  axs[1].hist(x=ts_hist[1], bins='auto', color='#0504aa', alpha=0.7, rwidth=0.85)
  axs[2].hist(x=ts_hist[2], bins='auto', color='#0504aa', alpha=0.7, rwidth=0.85)
  axs[3].hist(x=ts_hist[3], bins='auto', color='#0504aa', alpha=0.7, rwidth=0.85)
  axs[4].hist(x=ts_hist[4], bins='auto', color='#0504aa', alpha=0.7, rwidth=0.85)
  axs[5].hist(x=ts_hist[5], bins='auto', color='#0504aa', alpha=0.7, rwidth=0.85)

  axs[0].set_title('Left Wheel Encoder')
  axs[1].set_title('Right Wheel Encoder')
  axs[2].set_title('Lift Wheel Encoder')
  axs[3].set_title('Arm Encoder')
  axs[4].set_title('Pimu IMU ')
  axs[5].set_title('Wacc Acc')
  plt.show()

