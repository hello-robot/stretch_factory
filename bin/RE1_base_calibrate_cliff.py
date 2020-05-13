#!/usr/bin/env python


import time
import stretch_body.pimu as pimu
import math


p=pimu.Pimu()
old_zero=p.config['cliff_zero'][:]
p.config['cliff_zero'][0]=0
p.config['cliff_zero'][1]=0
p.config['cliff_zero'][2]=0
p.config['cliff_zero'][3]=0
p.startup()
print 'Ensure base is level on floor. Hit enter when ready'

raw_input()

cum=[0,0,0,0]
for k in range(100):
    p.pull_status()
    for i in range(4):
        cum[i]=cum[i]+p.status['cliff_range'][i]
    print 'Itr',k,'Val',p.status['cliff_range']
    time.sleep(0.05)
p.stop()
cum=[cum[0]/100.0,cum[1]/100.0,cum[2]/100.0,cum[3]/100.0]

for i in range(4):
    p.params['config']['cliff_zero'][i]=cum[i]

print '-------------------------'
print 'Prior zero of',old_zero
print 'Got zeros of',p.params['config']['cliff_zero']
print '-------------------------'
print('Write parameters to stretch_re1_factory_params.yaml (y/n)? [y]')
x=raw_input()
if len(x)==0 or x=='y' or x=='Y':
    print('Writing yaml...')
    p.write_device_params('pimu', p.params)