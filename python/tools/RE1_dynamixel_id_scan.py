#!/usr/bin/env python

from stretch_body.dynamixel_XL430 import DynamixelXL430, DynamixelCommError
import argparse
import stretch_body.device
d = stretch_body.device.Device(name='dummy_device') # to initialize logging config


parser=argparse.ArgumentParser(description='Scan a dynamixel bus by ID for servos')
parser.add_argument("usb", help="The dynamixel USB bus e.g.: /dev/hello-dynamixel-head")
parser.add_argument("--baud", help="Baud rate (57600, 115200, or 1000000) [57600]", type=int,default=0)
args = parser.parse_args()


if args.baud ==0:
    bauds = [57600, 115200]
else:
    bauds=[args.baud]

m=None
try:
    for b in bauds:
        print('----------------------------------------------------------')
        print('Scanning bus %s at baud rate %d' % (args.usb, b))
        for id in range(25):
                m = DynamixelXL430(id, args.usb,baud=b)
                try:
                    m.startup()
                except DynamixelCommError:
                    print("ping failed for ID and baud %d: "%(str(id),b))
                    continue
                m.do_ping()
                m.stop()
except (KeyboardInterrupt, SystemExit):
    if m is not None:
        m.stop()
