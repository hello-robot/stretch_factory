#!/usr/bin/env python
import argparse
import stretch_factory.param_mgmt as param_mgmt
import os
import stretch_body.hello_utils as hello_utils

def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        print('Invalid path: %s'%string)
        exit()

parser = argparse.ArgumentParser(description='Migrate Stretch parameter data to latest format')
group = parser.add_mutually_exclusive_group()
group.add_argument("--check", help="Check if current robot parameters require migration", action="store_true")
group.add_argument("--current", help="Display the current robot parameters", action="store_true")
group.add_argument("--future", help="Display proposed robot parameters after migration", action="store_true")
group.add_argument("--diff", help="Display differences between current and future parameters", action="store_true")
group.add_argument("--migrate", help="Migrate robot's paremters to latest format", action="store_true")
group.add_argument("--mgmt", help="Display overview on parameter management", action="store_true")
group.add_argument("--path", help="Path to robot parameters (if not $HELLO_FLEET_PATH/$HELLO_FLEET_ID)", type=dir_path)
args = parser.parse_args()

if args.path is None:
    fleet_dir=hello_utils.get_fleet_directory()
else:
    fleet_dir=args.path

print('Checking parameters found at: %s'%fleet_dir)
f=param_mgmt.get_robot_parameter_format(fleet_dir)
print('-------------------------------------')
print('Current parameter format is: %s'%f)
print('Required parameter format is: %s'%param_mgmt.latest_parameter_format)
if f==param_mgmt.latest_parameter_format:
    print('Parameter format is up to date. No migration is required.')
    exit()
if f=='Unknown':
    print('Unknown parameter format. Please contact Hello Robot support')
if f=='F0' and param_mgmt.latest_parameter_format=='F1':
    print('Migration is required to format F1')
    if hello_utils.confirm('Proceed?'):
        pass
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

