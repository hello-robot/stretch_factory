#!/usr/bin/env python

from stretch_body.dynamixel_XL430 import *
import argparse


parser=argparse.ArgumentParser(description='Change the baudrate of a servo')
parser.add_argument("usb", help="The dynamixel USB bus e.g.: /dev/hello-dynamixel-head")
parser.add_argument("id", help="The servo ID ", type=int)
parser.add_argument("baud", help="Baud rate (57600, 115200, or 1000000)", type=int)
args = parser.parse_args()

baud_rates=[57600,115200,1000000]
#print('Support baud rates:')
#print(baud_rates)
for b in baud_rates:
    print('---------------------')
    print('Checking servo current baud for %d'%b)
    print('----')
    m = DynamixelXL430(args.id, args.usb,baud=b)
    m.startup()
    m.disable_torque()
    if m.do_ping(verbose=False):
        print('Identified current baud of %d. Changing baud to %d'%(b,args.baud))
        m.set_baud_rate(args.baud)
        #m.stop()
        m2 = DynamixelXL430(args.id, args.usb, baud=args.baud)
        if m2.do_ping(verbose=False):
            print("Success at changing baud")
        else:
            print("Failed to change baud")
        exit()
    #m.stop()
