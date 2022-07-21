#!/usr/bin/env python

import stretch_body.dynamixel_hello_XL430 as dxl
from stretch_body.hello_utils import *

import argparse
import click

print_stretch_re_use()

parser = argparse.ArgumentParser(description='Calibrate the range of motion for select Dynamixel joints.')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--head_pan", help="Calibrate the head_pan joint", action="store_true")
group.add_argument("--head_tilt", help="Calibrate the head_tilt joint", action="store_true")
group.add_argument("--wrist_yaw", help="Calibrate the wrist_yaw joint", action="store_true")
args = parser.parse_args()

if click.confirm('About to calibrate the head pan. Doing so will require you to recalibrated your URDF. Proceed?'):
    if args.head_pan:
        h=dxl.DynamixelHelloXL430('head_pan')
    if args.head_tilt:
        h = dxl.DynamixelHelloXL430('head_tilt')
    if args.wrist_yaw:
        h = dxl.DynamixelHelloXL430('wrist_yaw')
    h.params['req_calibration']=1
    if not h.startup():
        exit(1)
    h.home(single_stop=False,move_to_zero=True,delay_at_stop=1.0,save_calibration=True, set_homing_offset=False)
    print('Recalibration done. Now redo the URDF calibration (see stretch_ros documentation)')
    h.stop()
