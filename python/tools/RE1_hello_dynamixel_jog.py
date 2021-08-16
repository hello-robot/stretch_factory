#!/usr/bin/env python


import sys
from stretch_body.dynamixel_hello_XL430 import *
from stretch_body.hello_utils import *


if len(sys.argv) < 2:
    raise Exception("Provide joint name, eg: RE1_hello_dynamixel_jog.py head_pan")
joint_name = sys.argv[1]


m = DynamixelHelloXL430(joint_name)
m.startup()


def menu_top():
    print('------ MENU -------')
    print('m: menu')
    print('a: increment position 5 deg')
    print('b: decrement position 5 deg')
    print('A: increment position 50 deg')
    print('B: decrement position 50 deg')
    print('q: got to position (deg)')
    print('p: ping')
    print('r: reboot')
    print('d: disable torque')
    print('e: enable torque')
    print('-------------------')

def step_interaction():
    m.pull_status()
    menu_top()
    x=sys.stdin.readline()
    if len(x)>1:
        if x[0]=='m':
            menu_top()
        if x[0]=='d':
            m.motor.disable_torque()
        if x[0]=='e':
            m.motor.enable_torque()
        if x[0]=='a':
            m.move_by(deg_to_rad(5.0))
        if x[0]=='b':
            m.move_by(deg_to_rad(-5.0))
        if x[0]=='A':
            m.move_by(deg_to_rad(50.0))
        if x[0]=='B':
            m.move_by(deg_to_rad(-50.0))
        if x[0]=='q':
            ff = float(x[2:])
            m.move_to(deg_to_rad(ff))
        if x[0] == 'p':
            if m.motor.do_ping():
                print('Ping success')
            else:
                print('Ping fail')
        if x[0] == 'r':
            m.motor.do_reboot()
    else:
        m.pretty_print()

try:
    while True:
        try:
            step_interaction()
        except (ValueError):
            print('Bad input...')
except (KeyboardInterrupt, SystemExit):
    m.shutdown()
