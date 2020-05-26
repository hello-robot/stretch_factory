#!/usr/bin/env python

import time
import stretch_body.arm as arm
import stretch_body.wrist_yaw as wrist_yaw
import stretch_body.lift as lift
import stretch_body.scope as scope
import yaml
import stretch_body.hello_utils as hu
import glob

import argparse

# ###################################

print 'This procuedure requires the range to have been first calibrated'
parser=argparse.ArgumentParser(description='Measure and test Lift guarded contact forces')
parser.add_argument("--test", help="Test current settings",action="store_true")
parser.add_argument("--measure", help="Measure forces",action="store_true")
parser.add_argument("--plot", help="Plot most recent calibration data",action="store_true")
args = parser.parse_args()


# ###################################
if args.plot:
    calibration_directory=hu.get_fleet_directory() + 'calibration_guarded_contact/'
    filenames = glob.glob(calibration_directory + '*lift_calibrate_guarded_contact_results' + '_*[0-9].yaml')
    filenames.sort()
    most_recent_filename = filenames[-1]
    print('Loading most recent calibration results from a YAML file named ' + most_recent_filename)

    fid = file(most_recent_filename, 'r')
    results = yaml.load(fid)
    fid.close()

    s = scope.Scope4(yrange=[-150,0], title='Force')
    print 'Hit enter to view down forces'
    raw_input()
    s.draw_array_xy(results['pos_down'][0], results['pos_down'][1], results['pos_down'][2], results['pos_down'][3],
                    results['force_down'][0], results['force_down'][1], results['force_down'][2], results['force_down'][3])
    print 'Hit enter to view up forces'
    raw_input()
    s = scope.Scope4(yrange=[0,100], title='Force')
    s.draw_array_xy(results['pos_up'][0], results['pos_up'][1], results['pos_up'][2], results['pos_up'][3],
                 results['force_up'][0], results['force_up'][1], results['force_up'][2], results['force_up'][3])
    print 'Hit enter to exit'
    raw_input()
    exit()
# ###################################

#Move arm /tool to safe position
a = arm.Arm()
a.startup()
a.motor.disable_sync_mode()
a.move_to(0.1)
a.push_command()
a.motor.wait_until_at_setpoint()
a.stop()

w=wrist_yaw.WristYaw()
w.startup()
w.move_to(0)
w.stop()

print 'Tool should be in a safe positon for full lift range-of-motion'
print 'Proceed? [y]'
x=raw_input()

if not (x=='y' or x=='Y' or len(x)==0):
    exit()

# ###################################
l = lift.Lift()
l.startup()
if not l.motor.status['pos_calibrated']:
    print 'Lift not yet homed'
    l.stop()
    exit()
l.motor.disable_sync_mode()

# ###################################
if args.test:
    l.motor.enable_guarded_mode()
    l.push_command()
    for i in range(4):
        l.move_to(l.params['range_m'][1])
        l.push_command()
        time.sleep(0.25)
        l.pull_status()
        ts = time.time()
        while not l.motor.status['near_pos_setpoint'] and not l.motor.status['in_guarded_event']:
            time.sleep(0.1)
            l.pull_status()

        l.move_to(l.params['range_m'][0])
        l.push_command()
        time.sleep(0.25)
        l.pull_status()
        ts = time.time()
        while not l.motor.status['near_pos_setpoint'] and not l.motor.status['in_guarded_event']:
            time.sleep(0.1)
            l.pull_status()

# ###################################
pos_top=l.params['range_m'][1]-.005
pos_bottom=l.params['range_m'][0] +.005
if args.measure:
    l.motor.disable_guarded_mode()
    l.push_command()
    l.move_to(pos_bottom)
    l.push_command()
    l.motor.wait_until_at_setpoint()
    print 'Starting data collection...'

    force_up=[[],[],[],[]]
    pos_up = [[], [], [], []]
    force_down=[[],[],[],[]]
    pos_down = [[], [], [], []]
    up_max=0
    down_min =0
    for i in range(4):
        l.move_to(pos_top)
        l.push_command()
        time.sleep(0.25)
        l.pull_status()
        ts = time.time()
        while not l.motor.status['near_pos_setpoint'] and time.time() - ts < 15.0:
            time.sleep(0.1)
            l.pull_status()
            force_up[i].append(l.status['force'])
            pos_up[i].append(l.status['pos'])
        up_max=max(up_max,max(force_up[i]))
        print('Up: Itr %d Len %d Max %f'%(i,len(force_up[i]),max(force_up[i])))

        l.move_to(pos_bottom)
        l.push_command()
        time.sleep(0.25)
        l.pull_status()
        ts = time.time()
        while not l.motor.status['near_pos_setpoint'] and time.time() - ts < 15.0:
            time.sleep(0.1)
            l.pull_status()
            force_down[i].append(l.status['force'])
            pos_down[i].append(l.status['pos'])
        print('Down: Itr %d Len %d Min %f' % (i, len(force_down[i]), min(force_down[i])))
        down_min = min(down_min, min(force_down[i]))


    results={'force_up':force_up,'force_down':force_down,'pos_up':pos_up,'pos_down':pos_down,'max_force_up':up_max, 'min_force_down':down_min}
    t = time.localtime()

    print 'Hit enter to view up forces'
    raw_input()
    s = scope.Scope4(yrange=[0,100], title='Force')
    s.draw_array_xy(pos_up[0],pos_up[1],pos_up[2],pos_up[3],force_up[0],force_up[1],force_up[2],force_up[3])

    print 'Hit enter to view down forces'
    raw_input()
    s = scope.Scope4(yrange=[-150,0], title='Force')
    s.draw_array_xy(pos_down[0],pos_down[1],pos_down[2],pos_down[3],force_down[0],force_down[1],force_down[2],force_down[3])

    margin_f = 15.0  # Margin beyond peak (N)
    print 'Using a margin of:',margin_f
    print 'Proposed limits are (N)',[down_min-margin_f,up_max + margin_f]
    print 'Nominal limits are (N) [-70, 70]'
    print 'Save to factory calibration? [y]'
    x=raw_input()

    if x=='y' or x=='Y' or len(x)==0:
        capture_date = str(t.tm_year) + str(t.tm_mon).zfill(2) + str(t.tm_mday).zfill(2) + str(t.tm_hour).zfill(2) + str(t.tm_min).zfill(2)
        filename = hu.get_fleet_directory() + 'calibration_guarded_contact/' + hu.get_fleet_id() + '_lift_calibrate_guarded_contact_results_' + capture_date + '.yaml'
        print 'Writing results:', filename
        with open(filename, 'w') as yaml_file:
            yaml.dump(results, yaml_file)
        l.params['contact_thresh_N'][0]=down_min-margin_f
        l.params['contact_thresh_N'][1] = up_max + margin_f
        l.write_device_params('lift',l.params)

l.stop()