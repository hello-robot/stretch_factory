#!/usr/bin/env python

from stretch_body.dynamixel_XL430 import *
import argparse


parser=argparse.ArgumentParser(description='Scan a dynamixel bus by ID for servos')
parser.add_argument("usb", help="The dynamixel USB bus e.g.: /dev/hello-dynamixel-head")
args = parser.parse_args()


m=None
try:
    for id in range(25):
        m = DynamixelXL430(id, args.usb)
        m.startup()
        m.do_ping()
        m.stop()
except (KeyboardInterrupt, SystemExit):
    if m is not None:
        m.stop()
