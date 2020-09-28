#!python


import time
import stretch_body.wacc as wacc
import math


w=wacc.Wacc()
w.startup()
print 'Ensure base is level and arm is retracted. Hit enter when ready'

raw_input()

cum=0.0
for i in range(100):
    w.pull_status()
    z=math.sqrt(w.status['ax']**2+w.status['ay']**2+w.status['az']**2)
    print 'Itr',i,'Val',z
    cum=cum+z
    time.sleep(0.05)
w.stop()
cum=cum/100.0
print 'Got a average value of',cum
s=9.80665/cum
print 'Scalar of',s
w.params['config']['accel_gravity_scale']=s
print('Write parameters to stretch_re1_factory_params.yaml (y/n)? [y]')
x=raw_input()
if len(x)==0 or x=='y' or x=='Y':
    print('Writing yaml...')
    w.write_device_params('wacc', w.params)