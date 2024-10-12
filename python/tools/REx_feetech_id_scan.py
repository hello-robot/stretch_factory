#!/usr/bin/env python3

from stretch_body.feetech_servo_sm import FeetechServoSM, FeetechCommError
import argparse
import sys
import stretch_body.hello_utils as hu
hu.print_stretch_re_use()

import stretch_body.device
d = stretch_body.device.Device(name='dummy_device',req_params=False) # to initialize logging config

parser=argparse.ArgumentParser(description='Scan a feetech bus by ID for servos')
parser.add_argument("usb_full_path", help="The full path to dynamixel USB bus e.g.: /dev/ttyUSB0")
args = parser.parse_args()

m=None
nfind=0
try:
    baudrates=[115200,1000000]
    for b in baudrates:
        print('------------')
        print('Scanning bus %s at baudrate %d' % (args.usb_full_path,b))
        result=FeetechServoSM.list_servos(args.usb_full_path,b)
        if len(result):
            print('Found %d  servos on bus %s' % (len(result), args.usb_full_path))
            break
except (KeyboardInterrupt, SystemExit):
    print('Error while scanning bus')


