#!/usr/bin/env python


import sys
import stretch_body.stepper as stepper


if len(sys.argv) < 2:
    raise Exception("Provide motor name e.g.: stepper_jog.py hello-motor1")
motor_name = sys.argv[1]

motor = stepper.Stepper('/dev/'+motor_name)
motor.startup()

i=0
try:
    while (True):
        motor.set_load_test()
        motor.push_command()
        print 'Iteration',i,'Read errors',motor.transport.status['read_error']
        i=i+1
except:
    motor.stop()


