#!/usr/bin/env python
from future.builtins import input
import os, sys
import math
import time
import stretch_body.wacc as wacc

print('Calibrating Wacc. Ensure arm is retracted and level to ground')
input('Hit enter when ready')


w=wacc.Wacc()
w.params['config']['accel_gravity_scale']=1.0
w.startup()

# Calibrate accel
cum=0.0
for i in range(100):
    w.pull_status()
    z=math.sqrt(w.status['ax']**2+w.status['ay']**2+w.status['az']**2)
    print('Itr',i,'Val',z)
    cum=cum+z
    time.sleep(0.05)
w.stop()
cum=cum/100.0
print('Got a average value of',cum)
s=9.80665/cum
accel_gravity_scale_max= 1.1
accel_gravity_scale_min= 0.9
if s>accel_gravity_scale_min and s<accel_gravity_scale_max:
    print('Gravity scalar of %f within bounds of %f to %f'%(s,accel_gravity_scale_min ,accel_gravity_scale_max ))
    w.params['config']['accel_gravity_scale']=s
    print('Writing yaml...')
    w.write_device_params('wacc', w.params)

else:
    print('Gravity scalar of %f outside bounds of %f to %f' % (s, q.params['accel_gravity_scale_min'], q.params['accel_gravity_scale_max']))
w.stop()
