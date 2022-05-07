#!/usr/bin/env python
import argparse
import stretch_factory.param_mgmt as param_mgmt
import os
import stretch_body.hello_utils as hello_utils
from os.path import exists
import click

def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        print('Invalid path: %s'%string)
        exit()

parser = argparse.ArgumentParser(description='Migrate Stretch parameter data to latest format')
group = parser.add_mutually_exclusive_group()
group.add_argument("--no_prompt", help="Don't use prompts", action="store_true")
group.add_argument("--mgmt", help="Display overview on parameter management", action="store_true")
group.add_argument("--path", help="Path to robot parameters (if not $HELLO_FLEET_PATH/$HELLO_FLEET_ID)", type=dir_path)
args = parser.parse_args()

if args.path is None:
    fleet_dir=hello_utils.get_fleet_directory()
else:
    fleet_dir=args.path
fleet_dir=fleet_dir.rstrip('/')
fleet_path=fleet_dir[:-17]
fleet_id=fleet_dir[-16:]

# Point to the data to be migrated
hello_utils.set_fleet_directory(fleet_path, fleet_id)

print('Checking parameters found at: %s'%fleet_dir)
print('-------------------------------------')
if exists(hello_utils.get_fleet_directory()+'stretch_user_params.yaml') and exists(hello_utils.get_fleet_directory()+'stretch_configuration_params.yaml'):
    print('Parameter format is up to date. No migration is required.')
    exit()

if click.confirm('Migration is required for robot %s. Proceed?'%fleet_id):
    if 1:#try:
        O, U, R=param_mgmt.migrate_params_RE1P0(fleet_path, fleet_id)
        print('Migration complete. Starting validation...')

        #Read in the new parameter data
        import stretch_body.robot_params
        (UU, RR) = stretch_body.robot_params.RobotParams().get_params()

        # Now check for differences
        added_warnings = param_mgmt.param_added_check(RR, R, 0, 'NewParams', 'OldParams',whitelist=['stall_backoff'])
        dropped_warnings = param_mgmt.param_dropped_check(RR, R, 0, 'NewParams', 'OldParams',whitelist=['factory_params'])
        change_warnings = param_mgmt.param_change_check(RR, R, 0, 'NewParams', 'OldParams',whitelist=['pid'])

        print('Validation check: Added %d, Dropped %d, Changed %d' % (added_warnings, dropped_warnings, change_warnings))
        print('Validation check should report 0 warnings. Reported total of %d' % (added_warnings+dropped_warnings+change_warnings))
        if click.confirm('Use new parameters for robot %s?'%fleet_id):
            uf=hello_utils.get_fleet_directory()+'stretch_re1_user_params.migration_backup.%s.yaml'%(hello_utils.create_time_string())
            os.system('mv %s %s' % (hello_utils.get_fleet_directory() + 'stretch_re1_user_params.yaml', uf))
            print('Moving %s to %s' % (hello_utils.get_fleet_directory() + 'stretch_re1_user_params.yaml', uf))
            ff = hello_utils.get_fleet_directory() + 'stretch_re1_factory_params.migration_backup.%s.yaml' % (hello_utils.create_time_string())
            os.system('mv %s %s' % (hello_utils.get_fleet_directory() + 'stretch_re1_factory_params.yaml', ff))
            print('Moving %s to %s' % (hello_utils.get_fleet_directory() + 'stretch_re1_factory_params.yaml', ff))
            print("Robot %s now configured to use latest parameter format"%fleet_id)
        else:
            uf=fleet_path+'/log/stretch_user_params.migration_backup.%s.%s.yaml'%(fleet_id,hello_utils.create_time_string())
            os.system('mv %s %s'% (hello_utils.get_fleet_directory()+'stretch_user_params.yaml',uf))
            print('Moving %s to %s'%(hello_utils.get_fleet_directory()+'stretch_user_params.yaml',uf))
            cf = fleet_path + '/log/stretch_configuration_params.migration_backup.%s.%s.yaml' % (fleet_id, hello_utils.create_time_string())
            os.system('mv %s %s' % (hello_utils.get_fleet_directory() + 'stretch_configuration_params.yaml', uf))
            print('Moving %s to %s' % (hello_utils.get_fleet_directory() + 'stretch_configuration_params.yaml', uf))
    # except:
    #     #Cleanup
    #     if exists(hello_utils.get_fleet_directory() + 'stretch_user_params.yaml'):
    #         os.system('rm %s'%hello_utils.get_fleet_directory() + 'stretch_user_params.yaml')
    #     if exists(hello_utils.get_fleet_directory() + 'stretch_configuration_params.yaml'):
    #         os.system('rm %s' % hello_utils.get_fleet_directory() + 'stretch_configuration_params.yaml')
else:
    exit()


mgmt = """
PARAMETER MANAGEMENT
--------------------
 
"""


# if args.check:
#     f=mgmt.get_robot_parameter_format(fleet_dir)
#
# if args.mgmt:
#     print(mgmt)
#     exit()

