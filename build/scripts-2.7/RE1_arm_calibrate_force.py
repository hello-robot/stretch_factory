#!python


import sys
import time
import stretch_body.arm as arm



# ######## Modify These ###############


import stretch_body.scope as scope
scope_range = [-3,3]
scope_data = 'current'
s = scope.Scope(yrange=scope_range, title=scope_data)


a=arm.Arm()
a.startup()
a.motor.disable_sync_mode()
a.motor.disable_guarded_mode()
a.push_command()

print 'Place force gauge in peak mode (N)'
print 'Hit enter to measure extension force (N)'
raw_input()

i_max=a.motor.status['current']
ts=time.time()
a.move_by(x_m= 0.1, v_m=a.params['motion']['slow']['vel_m'], a_m=a.params['motion']['slow']['accel_m'],req_calibration=False)
a.push_command()


while time.time()-ts<6.0:
    a.pull_status()
    s.step_display(a.motor.status['current'])
    print 'IMax', i_max
    if abs(a.motor.status['current'])>i_max:
        i_max=abs(a.motor.status['current'])
    time.sleep((0.1))
a.stop()

print 'Enter the peak force (N)'
x=sys.stdin.readline()
peak_force=float(x[0:])
c=peak_force/i_max
print('Calibration of %0.4f N/A'%c)


