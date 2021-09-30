#!/usr/bin/env python

import argparse
import subprocess
import os
import sys
from stretch_factory.device_mgmt import StretchDeviceMgmt


if os.geteuid() == 0:
    s = StretchDeviceMgmt()
    parser = argparse.ArgumentParser(description='Software reset of Stretch USB devices')
    parser.add_argument("--hello-motor-lift", help="Reset Lift USB", action="store_true")
    parser.add_argument("--hello-motor-right-wheel", help="Reset Right Wheel USB", action="store_true")
    parser.add_argument("--hello-motor-left-wheel", help="Reset Left Wheel USB", action="store_true")
    parser.add_argument("--hello-motor-arm", help="Reset Arm USB", action="store_true")
    parser.add_argument("--hello-pimu", help="Reset Pimu USB", action="store_true")
    parser.add_argument("--hello-wacc", help="Reset Wacc USB", action="store_true")
    parser.add_argument("--hello-dynamixel-wrist", help="Reset Wrist USB", action="store_true")
    parser.add_argument("--hello-dynamixel-head", help="Reset Head USB", action="store_true")

    args = parser.parse_args()
    if args.hello_motor_lift:
        s.reset('hello-motor-lift')
    if args.hello_motor_arm:
        s.reset('hello-motor-arm')
    if args.hello_motor_left_wheel:
        s.reset('hello-motor-left_wheel')
    if args.hello_motor_right_wheel:
        s.reset('hello-motor-right-wheel')
    if args.hello_pimu:
        s.reset('hello-pimu')
    if args.hello_wacc:
        s.reset('hello-wacc')
    if args.hello_dynamixel_head:
        s.reset('hello-dynamixel-head')
    if args.hello_dynamixel_wrist:
        s.reset('hello-dynamixel-wrist')

    if not any([args.hello_motor_lift, args.hello_motor_arm, args.hello_motor_left_wheel,args.hello_motor_right_wheel,args.hello_pimu,args.hello_wacc,args.hello_dynamixel_head,args.hello_wacc,args.hello_dynamixel_wrist]):
        s.reset_all()

else:
    subprocess.call(['sudo', 'python'] + sys.argv)
