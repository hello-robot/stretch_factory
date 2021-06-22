#!/usr/bin/env python


import sys
import stretch_body.stepper as stepper



if len(sys.argv) < 2:
    raise Exception("Provide motor name e.g.: stepper_calibration_flash_to_YAML.py hello-motor1")
motor_name = sys.argv[1]
motor = stepper.Stepper('/dev/'+motor_name)
if not motor.startup():
    exit()
data = motor.read_encoder_calibration_from_flash()
print('Read data of len',len(data))
print('Writing calibration data to YAML...')
motor.write_encoder_calibration_to_YAML(data)




