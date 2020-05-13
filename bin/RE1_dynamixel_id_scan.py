#!/usr/bin/env python


import sys
from stretch_body.dynamixel_XL430 import *

if len(sys.argv) < 2:
    raise Exception("Provide usb path and ID e.g.: dynamixel_id_scan.py /dev/hello-dynamixel-head")
usb = sys.argv[1]


m=None
try:
    for id in range(20):
        m = DynamixelXL430(id, usb)
        m.startup()
        m.do_ping()
        m.stop()
except (KeyboardInterrupt, SystemExit):
    if m is not None:
        m.stop()
