#!/usr/bin/env python3

import stretch_body.stretch_gripper as gripper
import time
import argparse

parser=argparse.ArgumentParser(description='Calibate the griper range and zero')
args=parser.parse_args()


g=gripper.StretchGripper()
g.startup()

#Good starting point
g.params['zero_t']=4000
g.params['range_t']=[0,8500]

print 'Hit enter to find zero'
raw_input()
g.home()
print('---------------------------------------------------')
print('Enter 1 to open fingers. Enter 2 to close fingers. Enter 3 when the fingertips are just barely not touching.')
z_done=False
while not z_done:
    x = raw_input()
    if x=='1':
        g.move_by(5.0)
    elif x=='2':
        g.move_by(-5.0)
    elif x=='3':
        g.pull_status()
        print('Setting zero at:',g.status['pos_ticks'])
        g.params['zero_t']=g.status['pos_ticks']
        z_done=True
print('---------------------------------------------------')
print('Enter 1 to open fingers. Enter 2 to close fingers. Enter 3 when the fingertips are fully open, ')
print('and no further opening motion is possible')
z_done=False
while not z_done:
    x = raw_input()
    if x == '1':
        g.move_by(5.0)
    elif x == '2':
        g.move_by(-5.0)
    elif x == '3':
        g.pull_status()
        print('Setting open at:',g.status['pos_ticks'])
        g.params['range_t']=[0,g.status['pos_ticks']]
        z_done=True

print('Hit enter to close')
raw_input()
g.move_to(-100)
print('Hit enter to open')
raw_input()
g.move_to(50.0)
print('Hit enter to go to zero')
raw_input()
g.move_to(0.0)
time.sleep(4.0)
g.stop()


print('Save calibration [y]?')
x=raw_input()
if x=='y' or x=='Y' or x=='':
    g.write_device_params('stretch_gripper',g.params)

