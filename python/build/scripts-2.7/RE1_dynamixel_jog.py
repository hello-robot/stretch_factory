#!python


import sys
from stretch_body.dynamixel_XL430 import *

if len(sys.argv) < 3:
    raise Exception("Provide usb path and ID e.g.: tune_XL430.py /dev/hello-dynamixel-head 10")
usb = sys.argv[1]
id = int(sys.argv[2])

m = DynamixelXL430(id, usb)
m.startup()


if not m.do_ping():
    exit(0)


m.disable_torque()
#If servo somehow has wrong drive mode it may appear to not respond to vel/accel profiles
#Can reset it here by uncommenting
#m.set_drive_mode(vel_based=True,reverse=False)
m.enable_pos()
m.enable_torque()


def menu_top():
    print('------ MENU -------')
    print('m: menu')
    print('a: increment position 50 tick')
    print('b: decrement position 50 tick')
    print('A: increment position 500 ticks')
    print('B: decrement position 500 ticks')
    print('v: set profile velocity')
    print('u: set profile acceleration')
    print('z: zero position')
    print('q: got to position')
    print 'p: ping'
    print 'r: reboot'
    print 'w: set max pwm'
    print 't: set max temp'
    print 'i: set id'
    print 'd: disable torque'
    print 'e: enable torque'
    print '-------------------'

def step_interaction():
    menu_top()
    x=sys.stdin.readline()
    if len(x)>1:
        if x[0]=='m':
            menu_top()
        if x[0]=='d':
            m.disable_torque()
        if x[0]=='e':
            m.enable_torque()
        if x[0]=='a':
            m.go_to_pos(m.get_pos()+50)
        if x[0]=='b':
            m.go_to_pos(m.get_pos()-50)
        if x[0]=='A':
            m.go_to_pos(m.get_pos()+500)
        if x[0]=='B':
            m.go_to_pos(m.get_pos()-500)
        if x[0]=='z':
            m.disable_torque()
            m.zero_position(verbose=True)
            m.enable_torque()
        if x[0]=='v':
            v=int(x[2:])
            m.set_profile_velocity(v)
        if x[0]=='u':
            a=int(x[2:])
            m.set_profile_acceleration(a)
        if x[0]=='q':
            ff = int(x[2:])
            m.go_to_pos(ff)
        if x[0]=='t':
            tt = int(x[2:])
            m.disable_torque()
            m.set_temperature_limit(tt)
            m.enable_torque()
        if x[0]=='w':
            pp = int(x[2:])
            m.disable_torque()
            m.set_pwm_limit(pp)
            m.enable_torque()
        if x[0] == 'i':
            print 'You will need to exit program and restart with new ID. Hit enter to continue'
            raw_input()
            q = int(x[2:])
            m.disable_torque()
            m.set_id(q)
            m.enable_torque()
            print 'New id is',m.get_id()
        if x[0] == 'p':
            if m.do_ping():
                print 'Ping success'
            else:
                print 'Ping fail'
        if x[0] == 'r':
            m.do_reboot()
    else:
        m.pretty_print()

try:
    while True:
        try:
            step_interaction()
        except (ValueError):
            print('Bad input...')
except (KeyboardInterrupt, SystemExit):
    m.disable_torque()
