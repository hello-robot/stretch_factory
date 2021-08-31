#!/usr/bin/env python
from stretch_body.dynamixel_XL430 import *
from stretch_body.hello_utils import *
import argparse


parser=argparse.ArgumentParser(description='Reboot all of the Dynamixel servos on a bus')
parser.add_argument("usb", help="The dynamixel USB bus e.g.: /dev/hello-dynamixel-head")
parser.add_argument("--baud", help="Baud rate (57600, 115200, or 1000000) [57600]", type=int,default=57600)
args = parser.parse_args()

m=None
try:
    for id in range(25):
        m = DynamixelXL430(id, args.usb,baud=args.baud)
        #m.startup() #Don't startup as may be in error state
        if (m.do_ping(verbose=False)):
            m.do_reboot()
        else:
            m.stop()
except (KeyboardInterrupt, SystemExit):
    if m is not None:
        m.stop()
