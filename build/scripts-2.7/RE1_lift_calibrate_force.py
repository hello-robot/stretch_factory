#!python


import sys
import time
import stretch_body.lift as lift



# ######## Modify These ###############


import stretch_body.scope as scope
scope_range = [-3,3]
scope_data = 'current'
s = scope.Scope(yrange=scope_range, title=scope_data)


l=lift.Lift()
l.startup()
l.motor.disable_sync_mode()
#l.motor.disable_guarded_mode()
l.push_command()

print 'Place force gauge in peak mode (N)'
print 'Hit enter to measure downward peak force (N)'
raw_input()

i_max=l.motor.status['current']
ts=time.time()
l.move_by(x_m= -0.01, v_m=l.params['motion']['slow']['vel_m'], a_m=l.params['motion']['slow']['accel_m'],req_calibration=False)
l.push_command()


while time.time()-ts<4.0:
    l.pull_status()
    s.step_display(l.motor.status['current'])
    print 'IMax', i_max
    if abs(l.motor.status['current'])>i_max:
        i_max=abs(l.motor.status['current'])
    time.sleep((0.1))
l.stop()

print 'Enter the peak force (N)'
x=sys.stdin.readline()
peak_force=float(x[0:])
c=peak_force/i_max
print('Calibration of %f N/A'%c)


