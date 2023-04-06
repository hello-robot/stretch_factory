#!/usr/bin/env python

from stretch_factory.hello_device_utils import compile_arduino_firmware, burn_arduino_firmware
import os.path
import sys
import argparse
import time
import stretch_body.hello_utils as hu
from stretch_factory.firmware_updater import AvailableFirmware
from colorama import Fore, Style
import stretch_body.device

hu.print_stretch_re_use()

use_device = {'hello-motor-arm': False, 'hello-motor-right-wheel': False, 'hello-motor-left-wheel': False,
              'hello-pimu': False, 'hello-wacc': False, 'hello-motor-lift': False}

#Note: This is a simple alternative to REx_firmware_updater.py
parser = argparse.ArgumentParser(description='Tool to directly flash Stretch firmware to a ttyACM device', )

parser.add_argument("port", type=str, metavar='port',
                    help='Device Port E.g. /dev/ttyACM0, /dev/hello-pimu')

parser.add_argument("device", type=str, metavar='device_type',
                    choices=list(use_device.keys()),
                    help='Chose a device name E.g. hello-motor-lift')

args = parser.parse_args()


def does_stepper_have_encoder_calibration_YAML(device_name):
    d = stretch_body.device.Device(req_params=False)
    sn = d.robot_params[device_name]['serial_no']
    fn = 'calibration_steppers/' + device_name + '_' + sn + '.yaml'
    enc_data = stretch_body.hello_utils.read_fleet_yaml(fn)
    return len(enc_data) != 0

if args.port and args.device:
    port = args.port
    a = AvailableFirmware({args.device: True})
    if "hello-motor" in args.device:
        sketch_name = 'hello_stepper'
        if not does_stepper_have_encoder_calibration_YAML(args.device):
            print(Style.BRIGHT + Fore.YELLOW + f"WARNING: Encoder calibration data hasn't been stored. Storing it before proceeding" + Style.RESET_ALL)
            os.system(f"REx_stepper_calibration_flash_to_YAML.py {args.device}")
            time.sleep(3)

    elif "hello-pimu" in args.device:
        sketch_name = 'hello_pimu'
    elif "hello-wacc" in args.device:
        sketch_name = 'hello_wacc'
    else:
        print(Fore.RED + 'Invalid Device name')
        sys.exit()

    repo_path = os.path.expanduser('~/repos/stretch_firmware')
    if not os.path.exists(repo_path):
        print('Firmware not present')
        print('Clone https://github.com/hello-robot/stretch_firmware to ~/repos/stretch_firmware first')
        sys.exit()
    t = 'Choose a Firmware Version'
    print(Style.BRIGHT + t)
    print('=' * len(t))
    i = 0
    for v in a.versions[args.device]:
        v_s = v.to_string()
        print(f"[{i}] {v_s}")
        i = i + 1
    print('-' * len(t))
    x = input("Enter Version:")
    version = a.versions[args.device][i - 1].to_string()
    print(f"\nChoosen version: {version}" + Style.RESET_ALL)
    sys.stdout.write('.')
    sys.stdout.flush()
    os.system(f"cd {repo_path}; git pull; git checkout tags/{version}")

    if compile_arduino_firmware(sketch_name, repo_path):
        print(Fore.GREEN + f"Compiled Arduino Sketch:{sketch_name} Successfully." + Style.RESET_ALL)
        if burn_arduino_firmware(port, sketch_name, repo_path):
            print(Fore.GREEN + f"Burned Arduino Sketch:{sketch_name} Successfully to port:{port}." + Style.RESET_ALL)
            if sketch_name == 'hello_stepper' and 'hello-' in port:
                time.sleep(3)
                os.system(f"REx_stepper_calibration_YAML_to_flash.py {args.device}")
        else:
            print(Fore.RED + f"Failed to burn Arduino Sketch:{sketch_name} to port:{port}." + Style.RESET_ALL)
    else:
        print(Fore.RED + f"Failed to compile Arduino Sketch:{sketch_name}." + Style.RESET_ALL)
