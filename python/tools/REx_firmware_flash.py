#!/usr/bin/env python

from stretch_factory.hello_device_utils import compile_arduino_firmware, burn_arduino_firmware
import os.path
import sys
import argparse
import time
import stretch_body.hello_utils as hu
from stretch_factory.firmware_available import FirmwareAvailable
from colorama import Fore, Style
import stretch_body.device
import click
import stretch_factory.hello_device_utils as hdu
import serial

hu.print_stretch_re_use()

use_device = {'hello-motor-arm': False, 'hello-motor-right-wheel': False, 'hello-motor-left-wheel': False,
              'hello-pimu': False, 'hello-wacc': False, 'hello-motor-lift': False}

#Note: This is a simple alternative to REx_firmware_updater.py
parser = argparse.ArgumentParser(description='Tool to directly flash Stretch firmware to a ttyACM device', )

group = parser.add_mutually_exclusive_group()
group.add_argument("--map", help="Print mapping from ttyACMx to Hello devices", action="store_true")
group.add_argument('--flash', nargs=2, type=str, help='Flash firmware. E.g, --flash /dev/ttyACM0 hello-motor-arm')
group.add_argument('--boot', nargs=1, type=str, help='Place board in bootloader mode. E.g, --reset /dev/ttyACM0')


args = parser.parse_args()


def does_stepper_have_encoder_calibration_YAML(device_name):
    d = stretch_body.device.Device(req_params=False)
    sn = d.robot_params[device_name]['serial_no']
    fn = 'calibration_steppers/' + device_name + '_' + sn + '.yaml'
    enc_data = stretch_body.hello_utils.read_fleet_yaml(fn)
    return len(enc_data) != 0

if args.boot:
    hdu.place_arduino_in_bootloader(args.boot[0])
    exit()

if args.map:
    mapping = hdu.get_hello_ttyACMx_mapping()
    click.secho('------------------------------------------', fg="yellow", bold=True)
    for k in mapping['hello']:
        print('%s | %s' % (k, mapping['hello'][k]))
    click.secho('------------------------------------------', fg="yellow", bold=True)
    for k in mapping['ACMx']:
        print('%s | %s' % (k, mapping['ACMx'][k]))
    click.secho('------------------------------------------', fg="yellow", bold=True)
    print('')
    exit()

if args.flash:
    port = args.flash[0]
    device = args.flash[1]
    a = FirmwareAvailable({device: True})
    if "hello-motor" in device:
        sketch_name = 'hello_stepper'
        if not does_stepper_have_encoder_calibration_YAML(device):
            print(Style.BRIGHT + Fore.YELLOW + f"WARNING: Encoder calibration data hasn't been stored. Storing it before proceeding" + Style.RESET_ALL)
            os.system(f"REx_stepper_calibration_flash_to_YAML.py {device}")
            time.sleep(3)

    elif "hello-pimu" in device:
        sketch_name = 'hello_pimu'
    elif "hello-wacc" in device:
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
    for v in a.versions[device]:
        v_s = v.to_string()
        print(f"[{i}] {v_s}")
        i = i + 1
    print('-' * len(t))
    x = input("Enter Version:")
    version = a.versions[device][i - 1].to_string()
    print(f"\nChoosen version: {version}" + Style.RESET_ALL)
    sys.stdout.write('.')
    sys.stdout.flush()
    os.system(f"cd {repo_path}; git pull; git checkout tags/{version}")

    if compile_arduino_firmware(sketch_name, repo_path):
        print(Fore.GREEN + f"Compiled Arduino Sketch:{sketch_name} Successfully." + Style.RESET_ALL)
        hdu.place_arduino_in_bootloader(port)
        time.sleep(1.0)
        if burn_arduino_firmware(port, sketch_name, repo_path):
            print(Fore.GREEN + f"Burned Arduino Sketch:{sketch_name} Successfully to port:{port}." + Style.RESET_ALL)
            if sketch_name == 'hello_stepper' and 'hello-' in port:
                time.sleep(3)
                os.system(f"REx_stepper_calibration_YAML_to_flash.py {device}")
        else:
            print(Fore.RED + f"Failed to burn Arduino Sketch:{sketch_name} to port:{port}." + Style.RESET_ALL)
    else:
        print(Fore.RED + f"Failed to compile Arduino Sketch:{sketch_name}." + Style.RESET_ALL)
