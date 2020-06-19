#!/usr/bin/env python

import time
import stretch_body.arm as arm
import stretch_body.scope as scope
import yaml
import stretch_body.hello_utils as hu

import argparse
import glob

# ###################################


parser=argparse.ArgumentParser(description='Measure and test Arm guarded contact forces')
parser.add_argument("--test", help="Test current settings",action="store_true")
parser.add_argument("--measure", help="Measure forces",action="store_true")
parser.add_argument("--plot", help="Plot most recent calibration data",action="store_true")
parser.add_argument("--offset_out", help="Offset out range by 2mm",action="store_true")
parser.add_argument("--offset_in", help="Offset in range by 2mm",action="store_true")
args = parser.parse_args()



# ###################################
if args.plot:
    calibration_directory=hu.get_fleet_directory() + 'calibration_guarded_contact/'
    filenames = glob.glob(calibration_directory + '*arm_calibrate_guarded_contact_results' + '_*[0-9].yaml')
    filenames.sort()
    most_recent_filename = filenames[-1]
    print('Loading most recent calibration results from a YAML file named ' + most_recent_filename)

    fid = file(most_recent_filename, 'r')
    results = yaml.load(fid)
    fid.close()

    s = scope.Scope4(yrange=[-100, 100], title='Force')
    print 'Hit enter to view in forces'
    raw_input()
    s.draw_array_xy(results['pos_in'][0], results['pos_in'][1], results['pos_in'][2], results['pos_in'][3],
                    results['force_in'][0], results['force_in'][1], results['force_in'][2], results['force_in'][3])
    print 'Hit enter to view out forces'
    raw_input()
    s.draw_array_xy(results['pos_out'][0], results['pos_out'][1], results['pos_out'][2], results['pos_out'][3],
                 results['force_out'][0], results['force_out'][1], results['force_out'][2], results['force_out'][3])
    print 'Hit enter to exit'
    raw_input()
    exit()

# ###################################
a = arm.Arm()
a.startup()
a.motor.disable_sync_mode()
# ###################################
if args.test:
    a.motor.enable_guarded_mode()
    a.push_command()
    for i in range(4):
        a.move_to(a.params['range_m'][1])
        a.push_command()
        time.sleep(0.25)
        a.pull_status()
        ts = time.time()
        while not a.motor.status['near_pos_setpoint'] and not a.motor.status['in_guarded_event']:
            time.sleep(0.1)
            a.pull_status()

        a.move_to(a.params['range_m'][0])
        a.push_command()
        time.sleep(0.25)
        a.pull_status()
        ts = time.time()
        while not a.motor.status['near_pos_setpoint'] and not a.motor.status['in_guarded_event']:
            time.sleep(0.1)
            a.pull_status()

# ###################################
if args.offset_out:
    xpos_out=a.params['range_m'][1]-.002
else:
    xpos_out = a.params['range_m'][1]

if args.offset_in:
    xpos_in=a.params['range_m'][0] +.002
else:
    xpos_in = a.params['range_m'][0]


if args.measure:
    a.motor.disable_guarded_mode()
    a.push_command()
    a.move_to(a.params['range_m'][0])
    a.push_command()
    a.motor.wait_until_at_setpoint()
    print 'Starting data collection...'

    force_out=[[],[],[],[]]
    force_in=[[],[],[],[]]
    pos_out = [[], [], [], []]
    pos_in = [[], [], [], []]
    out_max=0
    in_min =0
    for i in range(4):
        a.move_to(xpos_out)
        a.push_command()
        time.sleep(0.25)
        a.pull_status()
        ts = time.time()
        while not a.motor.status['near_pos_setpoint'] and time.time() - ts < 10.0:
            time.sleep(0.1)
            a.pull_status()
            force_out[i].append(a.status['force'])
            pos_out[i].append(a.status['pos'])
        out_max=max(out_max,max(force_out[i]))
        print('Out: Itr %d Len %d Max %f'%(i,len(force_out[i]),max(force_out[i])))

        a.move_to(xpos_in)
        a.push_command()
        time.sleep(0.25)
        a.pull_status()
        ts = time.time()
        while not a.motor.status['near_pos_setpoint'] and time.time() - ts < 10.0:
            time.sleep(0.1)
            a.pull_status()
            force_in[i].append(a.status['force'])
            pos_in[i].append(a.status['pos'])
        print('In: Itr %d Len %d Min %f' % (i, len(force_in[i]), min(force_in[i])))
        in_min = min(in_min, min(force_in[i]))

    print 'Hit enter to view out forces'
    raw_input()
    s = scope.Scope4(yrange=[-60,60], title='Force')
    s.draw_array_xy(pos_out[0],pos_out[1],pos_out[2],pos_out[3],force_out[0],force_out[1],force_out[2],force_out[3])

    print 'Hit enter to view in forces'
    raw_input()
    s = scope.Scope4(yrange=[-60,60], title='Force')
    s.draw_array_xy(pos_in[0],pos_in[1],pos_in[2],pos_in[3],force_in[0],force_in[1],force_in[2],force_in[3])

    margin_f = 20.0  # Margin beyond peak (N)
    print 'Using a margin of:', margin_f
    print 'Proposed limits are (N)', [in_min-margin_f, out_max + margin_f]
    print 'Nominal limits are (N) [-55, 65]'
    print 'Save to factory calibration? [y]'
    x=raw_input()

    if x=='y' or x=='Y' or len(x)==0:
        results = {'force_out': force_out, 'force_in': force_in, 'pos_out': pos_out, 'pos_in': pos_in, 'max_force_extension': out_max,'min_force_retraction': in_min}
        t = time.localtime()
        capture_date = str(t.tm_year) + str(t.tm_mon).zfill(2) + str(t.tm_mday).zfill(2) + str(t.tm_hour).zfill(2) + str(t.tm_min).zfill(2)
        filename = hu.get_fleet_directory() + 'calibration_guarded_contact/' + hu.get_fleet_id() + '_arm_calibrate_guarded_contact_results_' + capture_date + '.yaml'
        print 'Writing results:', filename
        with open(filename, 'w') as yaml_file:
            yaml.dump(results, yaml_file)
        a.params['contact_thresh_N'][0]=in_min-margin_f
        a.params['contact_thresh_N'][1] = out_max + margin_f
        a.write_device_params('arm',a.params)

a.stop()