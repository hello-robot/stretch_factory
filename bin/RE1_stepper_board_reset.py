#!/usr/bin/env python


import sys
import stretch_body.stepper as stepper



if len(sys.argv) < 2:
    raise Exception("Provide motor name e.g.: stepper_board_reset.py hello-motor1")
motor_name = sys.argv[1]
motor = stepper.Stepper('/dev/'+motor_name)
motor.startup()
print 'Resetting Board. Restart process...'
motor.board_reset()
motor.push_command()



