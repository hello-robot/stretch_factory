#!/usr/bin/env python


import sys
from stretch_body.dynamixel_XL430 import *

if len(sys.argv) <4:
    raise Exception("Provide usb path and ID e.g.: dynamixel_id_change.py /dev/hello-dynamixel-head <from> <to>")
usb = sys.argv[1]
id_from= int(sys.argv[2])
id_to= int(sys.argv[3])

m = DynamixelXL430(id_from, usb)
m.startup()
if not m.do_ping():
    exit(0)


print 'Ready to change ID to',id_to,'. Hit enter to continue'
raw_input()
m.disable_torque()
m.set_id(id_to)


m = DynamixelXL430(id_to, usb)
m.startup()
if not m.do_ping():
    print 'Failed to set new ID'
else:
    print 'Success at setting ID to',id_to
