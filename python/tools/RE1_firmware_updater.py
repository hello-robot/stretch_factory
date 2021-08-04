#!/usr/bin/env python
import argparse
from stretch_factory.firmware_updater import *


parser = argparse.ArgumentParser(description='Upload Stretch firmware to microcontrollers')

group = parser.add_mutually_exclusive_group()
parser.add_argument("--status", help="Display the current firmware status", action="store_true")
group.add_argument("--update", help="Update to recommended firmware", action="store_true")
group.add_argument("--update_to", help="Update to a specific firmware version", action="store_true")
group.add_argument("--update_to_branch", help="Update to HEAD of a specific branch", action="store_true")
group.add_argument("--mgmt", help="Display overview on firmware management", action="store_true")

parser.add_argument("--pimu", help="Upload Pimu firmware", action="store_true")
parser.add_argument("--wacc", help="Upload Wacc firmware", action="store_true")
parser.add_argument("--arm", help="Upload Arm Stepper firmware", action="store_true")
parser.add_argument("--lift", help="Upload Lift Stepper firmware", action="store_true")
parser.add_argument("--left_wheel", help="Upload Left Wheel Stepper firmware", action="store_true")
parser.add_argument("--right_wheel", help="Upload Right Wheel Stepper firmware", action="store_true")

args = parser.parse_args()

mgmt = """
FIRMWARE MANAGEMENT
--------------------
The Stretch Firmware is managed by Git tags. 

The repo is tagged with versions as <Board>.v<Major>.<Minor>.<Bugfix><Protocol>
For example Pimu.v0.0.1p0

This same version is included the Arduino file Common.h and is burned to the board EEPROM. It 
can be read from Stretch Body as <device>.board_info

Each Stretch Body device (Stepper, Wacc, Pimu) includes a variable valid_firmware_protocol
For example, stepper.valid_firmware_protocol='p0'

The updater will determine the available firmware versions given the current Stretch Body that is installed on 
the default Python path.

The updater will then query each device to determine what firmware is currently flashed to the boards. It can then
recommend updates to the user.

WHEN UPDATING FIRMWARE CODE
----------------------
After updating the firmware
* Increment the version / protocol in the device's Common.h', eg
  #define FIRMWARE_VERSION "Pimu.v0.0.5p1"
* Tag with the full version name that matches Common.h , eg
  git tag -a Pimu.v0.0.5p1 -m "Pimu bugfix of foo"
*Push tag to remote
  git push origin --tags
* Check the code in to stretch_firmware

If there was a change in protocol number, also update Stretch Body
accordingly. For example in stepper.py:
    self.valid_firmware_protocol='p1'

TAGGING
--------
https://git-scm.com/book/en/v2/Git-Basics-Tagging

To see available tags
  git log --pretty=oneline 

To tag an older commit
  git tag -a Pimu.v0.0.5p1 <hash> -m "Pimu bugfix of foo"

Push tags
  git push origin --tags

Delete tags
  git tag -d Pimu.v0.0.5p1
  git push origin --delete  Pimu.v0.0.5p1
USER EXPERIENCE
----------------
The user may update Stetch Body version from time to time. After installing
a new version of Stretch Body, this firmware updater tools should be run. 
"""

if args.arm or args.lift or args.wacc or args.pimu or args.left_wheel or args.right_wheel:
    use_device={'hello-motor-lift':args.lift,'hello-motor-arm':args.arm, 'hello-motor-right-wheel':args.right_wheel, 'hello-motor-left-wheel':args.left_wheel,'hello-pimu':args.pimu,'hello-wacc':args.wacc}
else:
    use_device = {'hello-motor-lift': True, 'hello-motor-arm': True, 'hello-motor-right-wheel': True, 'hello-motor-left-wheel': True, 'hello-pimu': True, 'hello-wacc': True}

if args.mgmt:
    print(mgmt)
    exit()

if args.status or args.update or args.update_to or args.update_to_branch:
    c = CurrrentConfiguration(use_device)
    r = FirmwareRepo()
    u = FirmwareUpdater(use_device,c,r)
    if not u.startup():
        exit()
    c.pretty_print()
    print('')
    r.pretty_print_available_versions()
    print('')
    u.pretty_print_recommended()
    print('')
    print('')
    if args.update:
        u.do_update()
    elif args.update_to:
        u.do_update_to()
    elif args.update_to_branch:
        u.do_update_to_branch()
else:
    parser.print_help()

