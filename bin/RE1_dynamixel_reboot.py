#!/usr/bin/env python

import time
from stretch_body.dynamixel_XL430 import *
from stretch_body.hello_utils import *
import sys

if len(sys.argv) < 2:
    raise Exception("Provide usb path and ID e.g.: dynamixel_reboot.py /dev/hello-dynamixel-head")
usb = sys.argv[1]

m=None
try:
    for id in range(15):
        m = DynamixelXL430(id, usb)
        m.startup()
        if (m.do_ping(verbose=False)):
            m.do_reboot()
        else:
            m.stop()
except (KeyboardInterrupt, SystemExit):
    if m is not None:
        m.stop()
