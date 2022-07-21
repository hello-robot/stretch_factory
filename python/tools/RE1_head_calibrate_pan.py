#!/usr/bin/env python

import stretch_body.dynamixel_hello_XL430 as dxl
from stretch_body.hello_utils import *
from stretch_body.hello_utils import *
import stretch_body.hello_utils as hu
import argparse

hu.print_stretch_re_use()

parser=argparse.ArgumentParser(description='Calibate the head pan to its hardstop')
args=parser.parse_args()

x = input('About to calibrate the head pan. Doing so will require you to recalibrated your URDF. Proceed (y/n)?')
if x == 'y' or x == 'Y':
    h=dxl.DynamixelHelloXL430('head_pan')
    h.params['req_calibration']=1
    if not h.startup():
        exit(1)
    h.home(single_stop=True)
    print('Recalibration done. Now redo the URDF calibration (see stretch_ros documentation)')
    h.stop()
