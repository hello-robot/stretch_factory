#!/usr/bin/env python

import sys
from stretch_body.dynamixel_XL430 import *

if len(sys.argv) <4:
    raise Exception("Provide usb path, id and baudrate e.g.: dynamixel_set_baud.py  /dev/hello-dynamixel-head 13 57600")
usb = sys.argv[1]
id = int(sys.argv[2])
baud= int(sys.argv[3])


baud_rates=[9600,57600,115200,1000000,2000000,3000000,4000000,4500000]
print('Available baud rates:')
print(baud_rates)
for b in baud_rates:
    print('---------------------')
    print('Checking baud %d'%b)
    m = DynamixelXL430(id, usb,baud=b)
    if m.do_ping():
        print('Changing baud to %d'%baud)
        m.set_baud_rate(baud)
        m = DynamixelXL430(id, usb, baud=baud)
        if m.do_ping():
            print("Success at changing baud")
        else:
            print("Failed to change baud")
        exit()
