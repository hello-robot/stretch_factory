#!/usr/bin/env python
import stretch_body.hello_utils as hello_utils
import stretch_body.robot
from math import radians, degrees, atan2, sin, cos
import time
import click

import argparse

parser=argparse.ArgumentParser(description='Calibrate the wheel_separation_m parameter for the base to ensure accurate rotations.')
args = parser.parse_args()


def do_spin(robot, deg):
    wrapToPi = lambda theta_rad: atan2(sin(theta_rad), cos(theta_rad))
    print('############ TEST %f DEGREES ###############'%deg)
    print('')
    print('')



    # Manually rotate Stretch so the front edge of its base aligns with a line on the floor
    robot.pimu.runstop_event_trigger()
    robot.push_command()
    print('')
    raw_input('Press Enter when Stretch is aligned at the starting position')
    robot.pimu.runstop_event_reset()
    robot.push_command()
    time.sleep(1) # let the reset take effect
    # Get Stretch's estimate of the current position.
    robot_status = robot.get_status()
    theta_startPosition_rad = robot_status['base']['theta']

    # Rotate by a fixed amount.
    turn_rad = radians(deg)
    turn_rads = radians(20)
    turn_radss = radians(45)
    robot.base.rotate_by(turn_rad, v_r=turn_rads, a_r=turn_radss)
    robot.push_command()
    time.sleep(abs(turn_rad/turn_rads))
    time.sleep(3) # the previous sleep was a rough estimate of the duration (not including acceleration)

    # Get Stretch's estimate of the current position.
    robot_status = robot.get_status()
    theta_preManualRotation_rad = robot_status['base']['theta']

    # Now manually rotate Stretch to actually be at the desired orientation
    robot.pimu.runstop_event_trigger()
    robot.push_command()
    print('')
    raw_input('Press Enter when Stretch is actually at the target angle')
    robot.pimu.runstop_event_reset()
    robot.push_command()
    time.sleep(1) # let the reset take effect

    # Once done, get Stretch's estimate of the current position again
    robot_status = robot.get_status()
    theta_postManualRotation_rad = robot_status['base']['theta']

    # Compute the offset
    offset_rad = theta_postManualRotation_rad - theta_preManualRotation_rad

    # Print the results
    print('')
    print( '')
    print( 'Stretch thought it rotated: %6.2f deg' % degrees(wrapToPi(theta_preManualRotation_rad - theta_startPosition_rad)))
    print( '  ... but it was off by   : %6.2f deg' % degrees(wrapToPi(offset_rad)))
    print( '')
    print( '')

    pct_error=degrees(wrapToPi(offset_rad))/deg
    d=(pct_error+1)*robot.base.params['wheel_separation_m']
    print('Error of %f (pct)'%(pct_error*100))
    print('Used wheel seperation of: %6.4f'%robot.base.params['wheel_separation_m'])
    print('Recommended wheel_separation_m %6.4f'%d)
    return d

robot = stretch_body.robot.Robot()
robot.startup()
d0=do_spin(robot,360)
d1=do_spin(robot,720)
d2=do_spin(robot,-360)
d3=do_spin(robot,-720)

d_avg=(d0+d1+d2+d3)/4.0
print('Final result: wheel_separation_m of %6.4f'%d_avg)
if click.confirm('Would you like to save the result to user YAML?'):
    user_yaml=hello_utils.read_fleet_yaml('stretch_re1_user_params.yaml')
    if not 'base'in user_yaml:
        user_yaml['base']={}
    user_yaml['base']['wheel_separation_m']=d_avg
    hello_utils.write_fleet_yaml('stretch_re1_user_params.yaml',user_yaml)
