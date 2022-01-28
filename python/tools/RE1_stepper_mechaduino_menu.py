#!/usr/bin/env python


import sys
import time
import stretch_body.stepper as stepper


if len(sys.argv) < 2:
    raise Exception("Provide usb path e.g.: RE1_stepper_mechaduino_menu.py /dev/hello-motor-lift")
usb = sys.argv[1]
motor_name = usb[5:]
motor = stepper.Stepper(usb)
motor.startup()
motor.push_command()

motor.turn_menu_interface_on()
time.sleep(0.5)
motor.print_menu()

try:
    while True:
        print('Menu Command>')
        s = str(sys.stdin.readline())
        motor.menu_transaction(s)
except (KeyboardInterrupt, SystemExit):
    motor.turn_rpc_interface_on()
    motor.stop()

