#!python


import sys
import time
import stretch_body.base as base



# ######## Modify These ###############


import scope
scope_range = [-3,3]
scope_data = 'current'
sl = scope.Scope(yrange=scope_range, title=scope_data)
sr = scope.Scope(yrange=scope_range, title=scope_data)

b=base.Base()
b.startup()
b.left_wheel.disable_sync_mode()
b.left_wheel.disable_guarded_mode()
b.right_wheel.disable_sync_mode()
b.right_wheel.disable_guarded_mode()
b.push_command()
b.pull_status()

print 'Place force gauge in peak mode (N)'
print 'Hit enter to measure extension force (N)'
raw_input()

i_max_l=b.left_wheel.status['current']
i_max_r=b.right_wheel.status['current']

ts=time.time()
b.translate_by(x_m=0.1, v_m=0.2, a_m=0.2)
b.push_command()

while time.time()-ts<6.0:
    b.pull_status()
    sl.step_display(b.left_wheel.status['current'])
    sr.step_display(b.right_wheel.status['current'])
    print 'IMax', i_max_l, i_max_r
    if abs(b.left_wheel.status['current'])>i_max_l:
        i_max_l=abs(b.left_wheel.status['current'])
    if abs(b.right_wheel.status['current'])>i_max_r:
        i_max_r=abs(b.right_wheel.status['current'])
    time.sleep((0.1))
b.stop()

print 'Enter the peak force (N)'
x=sys.stdin.readline()
peak_force=float(x[0:])
cl=peak_force/i_max_l/2
cr=peak_force/i_max_r/2
ca=(cl+cr)/2
print('Calibration-Left Wheel of %0.4f N/A'%cl)
print('Calibration-Right Wheel of %0.4f N/A'%cr)
print('Average calibration of %0.4f N/A'%ca)


