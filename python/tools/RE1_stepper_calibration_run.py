#!/usr/bin/env python

from future.builtins import input
import sys
import time
import stretch_body.stepper as stepper



if len(sys.argv) < 2:
    raise Exception("Provide motor name e.g.: stepper_run_calibration.py hello-motor1")
motor_name = sys.argv[1]
motor = stepper.Stepper('/dev/'+motor_name)
motor.startup()
motor.push_command()
motor.turn_menu_interface_on()

time.sleep(0.5)
#motor.print_menu()

calibration_done=False


i=0
while i<3 and not calibration_done:
    print('Doing step ',i)
    motor.menu_transaction('s')
    yn=input('Did motor step (y/n)[n]?')
    i=i+1
    if yn=='y':
        print('Starting encoder calibration')
        motor.menu_transaction('c')
        calibration_done=True
        input('Hit enter when calibration done...')
        break
if calibration_done:
    print('Calibration success.')
else:
    print('Calibration failure')
motor.turn_rpc_interface_on()
motor.push_command()
motor.board_reset()
motor.push_command()


