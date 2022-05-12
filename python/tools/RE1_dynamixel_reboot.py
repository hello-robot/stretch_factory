#!/usr/bin/env python
from stretch_body.dynamixel_XL430 import *
from stretch_body.hello_utils import *
import argparse
import stretch_body.device
d = stretch_body.device.Device(name='dummy_device') # to initialize logging config


parser=argparse.ArgumentParser(description='Reboot all of the Dynamixel servos on a bus')
parser.add_argument("usb", help="The dynamixel USB bus e.g.: /dev/hello-dynamixel-head")
parser.add_argument("--baud", help="Baud rate (57600, 115200, or 1000000) [57600]", type=int,default=0)
args = parser.parse_args()

m=None
num_reboots=0
if args.baud ==0:
    bauds = [57600, 115200]
else:
    bauds=[args.baud]
try:
    for id in range(25):
            for b in bauds:
                m = DynamixelXL430(id, args.usb,baud=b)
                #m.startup() #Don't startup as may be in error state
                if (m.do_ping(verbose=False)):
                    print('Rebooting device %d on bus %s'%(id,args.usb))
                    m.do_reboot()
                    num_reboots=num_reboots+1
                    break
                else:
                    m.stop()
    print('Rebooted %d devices'%num_reboots)
except (KeyboardInterrupt, SystemExit):
    if m is not None:
        m.stop()
