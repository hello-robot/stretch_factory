#!/usr/bin/env python
from stretch_body.hello_utils import *
import stretch_body.scope
import argparse
import click

print_stretch_re_use()

parser = argparse.ArgumentParser(description='Calibrate the default guarded contacts for a joint.')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--lift", help="Calibrate the head_pan joint", action="store_true")
group.add_argument("--arm", help="Calibrate the head_tilt joint", action="store_true")
parser.add_argument("--ncycle", type=int,help="Number of sweeps to run",default=4)
args = parser.parse_args()

contact_model='current_A'

if args.lift:
    import stretch_body.lift
    j=stretch_body.lift.Lift()
if args.arm:
    import stretch_body.arm
    j=stretch_body.arm.Arm()

if not j.startup(threaded=False):
    exit(1)

j.pull_status()
if not j.motor.status['pos_calibrated']:
    print('Joint not calibrated. Exiting.')
    exit(1)


if (j.name in j.user_params and 'contact_models' in j.user_params[j.name]) and ('current_A' in j.user_params[j.name]['contact_models']) \
        and ('contact_thresh_default' in j.user_params[j.name]['contact_models']['current_A']):
    click.secho('------------------------',fg="yellow")
    click.secho('NOTE: This tool updates contact_thresh_default for %s in stretch_configuration_params.yaml'%j.name.upper(),fg="yellow")
    click.secho('NOTE: Your stretch_user_params.yaml overrides contact_thresh_default for %s'%j.name.upper(),fg="yellow")
    click.secho('NOTE: As such, the updated calibration will not change the contact behavior unless you remove the user params.',fg="yellow")
click.secho('------------------------',fg="yellow")
click.secho('Joint %s will go through its full range-of-motion. Ensure workspace is collision free '%j.name.capitalize(),fg="yellow")
if click.confirm('Proceed?'):
    j.motor.disable_sync_mode()
    xpos_pos=j.params['range_m'][1]
    xpos_neg=j.params['range_m'][0]
    j.motor.disable_guarded_mode()
    j.push_command()
    j.move_to(xpos_neg)
    j.push_command()
    j.motor.wait_until_at_setpoint()

    log_dir = get_stretch_directory('log/')
    log_file_ts=create_time_string()
    log_file_prefix='calibrate_guarded_contact_{0}'.format(j.name)
    print('')
    print('------------------------------------')
    print('Starting data collection...')

    current_pos = [[], [], [], []]
    current_neg = [[], [], [], []]
    pos_out = [[], [], [], []]
    pos_in = [[], [], [], []]
    max_current_pos = 0
    min_current_neg = 0
    for i in range(args.ncycle):
        j.move_to(xpos_pos)
        j.push_command()
        time.sleep(0.25)
        j.pull_status()
        ts = time.time()
        while not j.motor.status['near_pos_setpoint'] and time.time() - ts < 10.0:
            time.sleep(0.1)
            j.pull_status()
            current_pos[i].append(j.motor.status['current'])
            pos_out[i].append(j.status['pos'])
        max_current_pos = max(max_current_pos, max(current_pos[i]))
        print('Positive Motion: Itr %d  Max %f (A)' % (i, max(current_pos[i])))
    
        j.move_to(xpos_neg)
        j.push_command()
        time.sleep(0.25)
        j.pull_status()
        ts = time.time()
        while not j.motor.status['near_pos_setpoint'] and time.time() - ts < 10.0:
            time.sleep(0.1)
            j.pull_status()
            current_neg[i].append(j.motor.status['current'])
            pos_in[i].append(j.status['pos'])
        print('Negative Motion: Itr %d Min %f (A)' % (i,  min(current_neg[i])))
        min_current_neg = min(min_current_neg, min(current_neg[i]))
    results = {'current_pos': current_pos, 'current_neg': current_neg, 'pos_out': pos_out, 'pos_in': pos_in, 'max_current_pos': max_current_pos,'min_current_neg': min_current_neg}
    print('Maximum current pos: %f'%max_current_pos)
    print("Minimum current neg: %f"%min_current_neg)
    print('--------------------------------------')
    print('')

    t = time.localtime()
    log_filename=log_dir+log_file_prefix+'_results_'+log_file_ts+'.log'
    print('Writing results log: %s'%log_filename)
    with open(log_filename, 'w') as yaml_file:
        yaml.dump(results, yaml_file)

    s = stretch_body.scope.Scope4(yrange=[j.motor.gains['iMax_neg']*1.1, j.motor.gains['iMax_pos']*1.1], title='Current Postive')
    s.draw_array_xy(pos_out[0], pos_out[1], pos_out[2], pos_out[3], current_pos[0], current_pos[1], current_pos[2], current_pos[3])
    img_filename=log_dir+log_file_prefix+'_pos_current_'+log_file_ts+'.png'
    print('Writing image log: %s' % img_filename)
    s.savefig(img_filename)

    s = stretch_body.scope.Scope4(yrange=[j.motor.gains['iMax_neg']*1.1, j.motor.gains['iMax_pos']*1.1], title='Current Negative')
    s.draw_array_xy(pos_in[0], pos_in[1], pos_in[2], pos_in[3], current_neg[0], current_neg[1], current_neg[2], current_neg[3])
    img_filename = log_dir + log_file_prefix + '_neg_current_' + log_file_ts + '.png'
    print('Writing image log: %s' % img_filename)
    s.savefig(img_filename)

    ocd_n = j.params['contact_models']['current_A']['contact_thresh_default'][0]
    ocd_p = j.params['contact_models']['current_A']['contact_thresh_default'][1]
    opct_n=j.motor.current_to_effort_pct(ocd_n)
    opct_p = j.motor.current_to_effort_pct(ocd_p)


    ncd_n = max(j.params['contact_models']['current_A']['contact_thresh_max'][0],
                min_current_neg - j.params['contact_models']['current_A']['contact_thresh_calibration_margin'])

    ncd_p = min(j.params['contact_models']['current_A']['contact_thresh_max'][1],
                max_current_pos +j.params['contact_models']['current_A']['contact_thresh_calibration_margin'])
    npct_n=j.motor.current_to_effort_pct(ncd_n)
    npct_p = j.motor.current_to_effort_pct(ncd_p)
    click.secho('')
    click.secho('Prior contact defaults were:',fg="green")
    click.secho('----------------------------')
    click.secho('Positive direction: %f (A) %f (Effort)'%(ocd_p,opct_p),fg="green")
    click.secho('Negative direction: %f (A) %f (Effort)'%(ocd_n,opct_n),fg="green")
    click.secho('')
    click.secho('New contact defaults are:',fg="green")
    click.secho('----------------------------')
    click.secho('Positive direction: %f (A) %f (Effort)'%(ncd_p,npct_p),fg="green")
    click.secho('Negative direction: %f (A) %f (Effort)'%(ncd_n,npct_n),fg="green")

    if click.confirm('Save results?'):
        j.write_configuration_param_to_YAML(j.name + '.contact_models.current_A.contact_thresh_default', [ncd_n,ncd_p])


# ao = max_current_pos +q.params['margin_N']
# ai= min_current_neg-q.params['margin_N']
# print('-------------------------------------')
# print('Using a margin of:',q.params['margin_N'])
# print('Proposed limits are (N)',[ai,ao])
# print('Nominal limits are (N)',[q.params['nominal_current_neg_N'],q.params['nominal_current_pos_N']])
#
# if ai>(q.params['nominal_current_neg_N']-q.params['within_nominal_N']) and ao<(q.params['nominal_current_pos_N']+q.params['within_nominal_N']):
#     print('Measurement within %s of nominal limits. Saving data'%q.params['within_nominal_N'])
#     filename = hu.get_fleet_directory() + 'calibration_guarded_contact/' + hu.get_fleet_id() + '_arm_calibrate_guarded_contact_results_' + hu.create_time_string() + '.yaml'
#     print('Writing results:', filename)
#     with open(filename, 'w') as yaml_file:
#         yaml.dump(results, yaml_file)
#     j.params['contact_thresh_N'][0]=ai
#     j.params['contact_thresh_N'][1] =ao
#     j.write_configuration_param_to_YAML('arm.contact_thresh_N', j.params['contact_thresh_N'])
# else:
#     print('-------------------------------------')
#     print('Measurements out of nominal limits. Exiting.')
#     q.write_test_result(message='Exceeded nominal limits', pass_test=0)
#     j.stop()
#     exit()


# ###################################
# print('-------------------------------------')
# print('Beginning validation test. Manually grab the arm while it is in motion.')
# j.motor.enable_guarded_mode()
# j.push_command()
# for i in range(4):
#     j.move_to(j.params['range_m'][1])
#     j.push_command()
#     time.sleep(0.25)
#     j.pull_status()
#     ts = time.time()
#     while not j.motor.status['near_pos_setpoint'] and not j.motor.status['in_guarded_event']:
#         time.sleep(0.1)
#         j.pull_status()
#
#     j.move_to(j.params['range_m'][0])
#     j.push_command()
#     time.sleep(0.25)
#     j.pull_status()
#     ts = time.time()
#     while not j.motor.status['near_pos_setpoint'] and not j.motor.status['in_guarded_event']:
#         time.sleep(0.1)
#         j.pull_status()