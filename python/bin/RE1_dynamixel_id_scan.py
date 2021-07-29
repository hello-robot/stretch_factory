#!/usr/bin/env python

from stretch_body.dynamixel_XL430 import DynamixelXL430, DynamixelCommError
import argparse


parser=argparse.ArgumentParser(description='Scan a dynamixel bus by ID for servos')
parser.add_argument("usb", help="The dynamixel USB bus e.g.: /dev/hello-dynamixel-head")
parser.add_argument("--baud", help="Baud rate (57600, 115200, or 1000000) [57600]", type=int,default=57600)
args = parser.parse_args()

print('Scanning bus %s at baud rate %d'%(args.usb,args.baud))
print('----------------------------------------------------------')
m=None
try:
    for id in range(25):
        m = DynamixelXL430(id, args.usb,baud=args.baud)
        try:
            m.startup()
        except DynamixelCommError:
            print("ping failed for ID: " + str(id))
            continue
        m.do_ping()
        m.stop()
except (KeyboardInterrupt, SystemExit):
    if m is not None:
        m.stop()
