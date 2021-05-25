#!/usr/bin/env python
from stretch_body.dynamixel_XL430 import *
import argparse


parser=argparse.ArgumentParser(description='Set the ID of a Dynamixel servo')
parser.add_argument("usb", help="The dynamixel USB bus e.g.: /dev/hello-dynamixel-head")
parser.add_argument("id_from", help="The ID to change from", type=int)
parser.add_argument("id_to", help="The ID to change to", type=int)
args = parser.parse_args()



m = DynamixelXL430(args.id_from, args.usb)
m.startup()
if not m.do_ping():
    exit(0)


print('Ready to change ID %d to %d. Hit enter to continu'%(args.id_from,args.id_to))
raw_input()
m.disable_torque()
m.set_id(args.id_to)


m = DynamixelXL430(args.id_to, args.usb)
m.startup()
if not m.do_ping():
    print('Failed to set new ID')
else:
    print('Success at setting ID to %d'%args.id_to)

