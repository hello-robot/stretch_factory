#!/usr/bin/env python
import sys
import os
import argparse
import click
import stretch_body.hello_utils as hu
from subprocess import Popen, PIPE
import git
import stretch_body.stepper
import stretch_body.pimu
import stretch_body.wacc

parser=argparse.ArgumentParser(description='Upload Stretch firmware to microcontrollers')
parser.add_argument("--config", help="Print current firmware configuration",action="store_true")
parser.add_argument("--available", help="Print available firmware configuration",action="store_true")
parser.add_argument("--recommended", help="Print recommend firmware upgrade / downgrade",action="store_true")
parser.add_argument("--update", help="Update to recommended firmware",action="store_true")
parser.add_argument("--pimu", help="Upload Pimu firmware",action="store_true")
parser.add_argument("--wacc", help="Upload Wacc firmware",action="store_true")
parser.add_argument("--arm", help="Upload Arm Stepper firmware",action="store_true")
parser.add_argument("--lift", help="Upload Lift Stepper firmware",action="store_true")
parser.add_argument("--left_wheel", help="Upload Left Wheel Stepper firmware",action="store_true")
parser.add_argument("--right_wheel", help="Upload Right Wheel Stepper firmware",action="store_true")

args=parser.parse_args()

"""
FIRMWARE MANAGEMENT
--------------------
The Stretch Firmware is managed by Git tags. 

The repo is tagged with versions as <Board>.v<Major>.<Minor>.<Bugfix><Protocol>
For example Pimu.v0.0.1p0

This same version is included the file Common.h and is burned to the board EEPROM. It 
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

class CurrrentConfiguration():
    def __init__(self):
        self.config_info={'hello-motor-lift': {},'hello-motor-arm':{},'hello-motor-left-wheel':{},'hello-motor-right-wheel':{},'hello-pimu':{},'hello-wacc':{}}
        for device in self.config_info.keys():
            if device=='hello-wacc':
                dd=stretch_body.wacc.Wacc()
            elif device == 'hello-pimu':
                dd = stretch_body.pimu.Pimu()
            else:
                dd=stretch_body.stepper.Stepper('/dev/'+device)
            dd.startup()
            if dd.board_info['firmware_version'] is not None: #Was able to pull board info from device
                self.config_info[device]['board_info'] = dd.board_info.copy()
                self.config_info[device]['valid_firmware_protocol']=dd.valid_firmware_protocol
                self.config_info[device]['protocol_match']=(dd.board_info['protocol_version']==dd.valid_firmware_protocol)
                dd.stop()

    def pretty_print(self):
        click.secho('############## Currently Installed Configuration ##############',fg="green", bold=True)
        for device in self.config_info:
            click.secho('---- %s ----'%device.upper(), fg="yellow",bold=True)
            if len(self.config_info[device]):
                click.echo('Installed Firmware: %s'%self.config_info[device]['board_info']['firmware_version'])
                click.echo('Stretch Body required protocol:%s'%self.config_info[device]['valid_firmware_protocol'])
                if self.config_info[device]['protocol_match']:
                    click.secho('Protocol match', fg="green")
                else:
                    click.secho('Protocol mismatch', fg="red")
            else:
                click.secho('Device not found',fg="red")

class FirmwareRepo():
    def __init__(self):
        self.repo=None
        self.repo_path=None
        self.versions = {'hello-motor-lift': [], 'hello-motor-arm': [], 'hello-motor-left-wheel': [],
                         'hello-motor-right-wheel': [], 'hello-pimu': [], 'hello-wacc': []}
        self.__clone_firmware_repo()
        self.__get_available_firmware_versions()

    def __clone_firmware_repo(self):
        self.repo_path = '/tmp/stretch_firmware_update_' + hu.create_time_string()
        print('Cloning latest version of Stretch Firmware to %s'% self.repo_path)
        git.Repo.clone_from('https://github.com/hello-robot/stretch_firmware',  self.repo_path)
        self.repo = git.Repo( self.repo_path)

    def cleanup(self):
        #Use with care!
        if self.repo_path is not None:
            os.system('rm -rf '+self.repo_path)

    def pretty_print_available_versions(self):
        click.secho('############## Currently Available Versions in Stretch Firmware ##############',fg="green", bold=True)
        for device_name in self.versions.keys():
            print('---- %s ----'%device_name.upper())
            for v in self.versions[device_name]:
                print(v)
    # python -m pip install gitpython
    # https://www.devdungeon.com/content/working-git-repositories-python
    def __get_available_firmware_versions(self):
        if self.repo is None:
            return
        for t in self.repo.tags:
            v = FirmwareVersion(t.name, t.commit.message)
            if v.valid:
                if v.device == 'Stepper':
                    self.versions['hello-motor-lift'].append(v)
                    self.versions['hello-motor-arm'].append(v)
                    self.versions['hello-motor-left-wheel'].append(v)
                    self.versions['hello-motor-right-wheel'].append(v)
                if v.device == 'Wacc':
                    self.versions['hello-wacc'].append(v)
                if v.device == 'Pimu':
                    self.versions['hello-pimu'].append(v)

    def get_most_recent_version(self,device_name,protocol):
        if len(self.versions[device_name])==0:
            return None
        recent=None
        for v in self.versions[device_name]:
            if v.same_protocol(int(protocol[1:])):
                if recent is None:
                    recent=v
                else:
                    if v>recent:
                        recent=v
        return recent

class FirmwareVersion():
    def __init__(self,x,commit_msg=''):
        self.device='NONE'
        self.major=0
        self.minor=0
        self.bugfix=0
        self.protocol=0
        self.valid=False
        self.commit_msg=commit_msg
        self.from_string(x)
    def __str__(self):
        return self.to_string()
    def to_string(self):
        return self.device+'.v'+str(self.major)+'.'+str(self.minor)+'.'+str(self.bugfix)+'p'+str(self.protocol)

    def __gt__(self, other):
            if self.major > other.major:
                return True
            if self.minor > other.minor:
                return True
            if self.bugfix > other.bugfix:
                return True
            return False

    def same_device(self,d):
        return d==self.device
    def same_protocol(self,p):
        return p==self.protocol

    def from_string(self,x):
        #X is of form 'Stepper.v0.0.1p0'
        try:
            xl=x.split('.')
            if len(xl) is not 4:
                raise Exception('Invalid version len')
            device=xl[0]
            if not (device=='Stepper' or device=='Wacc' or device=='Pimu'):
                raise Exception('Invalid device name ')
            major=int(xl[1][1:])
            minor=int(xl[2])
            bugfix=int(xl[3][0:xl[3].find('p')])
            protocol=int(xl[3][(xl[3].find('p')+1):])
            self.device=device
            self.major=major
            self.minor=minor
            self.bugfix=bugfix
            self.protocol=protocol
            self.valid=True
        except(ValueError,Exception):
            print('Invalid version format in tag: %s'%x)


class FirmwareUpdater():
    def __init__(self,current_config,repo):
        self.repo=repo
        self.current_config=current_config
        self.recommended = {'hello-motor-lift': None, 'hello-motor-arm': None, 'hello-motor-left-wheel': None,'hello-motor-right-wheel': None, 'hello-pimu': {}, 'hello-wacc': None}
        self.__get_recommend_updates()

    def __get_recommend_updates(self):
        for device_name in self.recommended.keys():
                cfg=self.current_config.config_info[device_name] #Dictionary of installed configuration for this device
                if len(cfg): #Len 0 if device not found
                    v = self.repo.get_most_recent_version(device_name, cfg['valid_firmware_protocol'])
                    self.recommended[device_name]=v

    def pretty_print_recommended(self):
        click.secho('############## Recommended Firmware Updates ##############', fg="green",bold=True)
        for device_name in self.recommended.keys():
            if self.recommended[device_name] is None:
                print('%s | No recommendation available'%device_name.upper().ljust(25))
            else:
                cfg = self.current_config.config_info[device_name]
                protocol_board = int(cfg['board_info']['protocol_version'][1:])
                protocol_required = int(cfg['valid_firmware_protocol'][1:])
                if protocol_required > protocol_board:
                    rec='Upgrade required to %s'%self.recommended[device_name]
                elif protocol_required < protocol_board:
                    rec = 'Downgrade required to %s' % self.recommended[device_name]
                else:
                    if self.recommended[device_name].to_string()==self.current_config.config_info[device_name]['board_info']['firmware_version']:
                        rec='At most recent version with %s' % self.recommended[device_name]
                    else:
                        rec = 'Update available to %s' % self.recommended[device_name]
                print('%s | %s | from %s' % (device_name.upper().ljust(25), rec.ljust(40),self.current_config.config_info[device_name]['board_info']['firmware_version']))


    def do_update(self):
        self.current_config.pretty_print()
        self.pretty_print_recommended()
        click.secho('------------------------------------------------', fg="yellow", bold=True)
        click.secho('WARNING: Updating robot firmware should only be done by experienced users', fg="yellow",bold=True)
        click.secho('WARNING: Do not have other robot processes running during update', fg="yellow",bold=True)
        click.secho('WARNING: Leave robot powered on during update', fg="yellow", bold=True)
        click.secho('WARNING: Ensure Lift as support clamp in place', fg="yellow", bold=True)
        click.secho('------------------------------------------------', fg="yellow", bold=True)
        if click.confirm('Proceed with update??'):
            if 1:
                for device_name in self.recommended.keys():
                    if self.recommended[device_name] is not None:
                        if not (self.recommended[device_name].to_string()==self.current_config.config_info[device_name]['board_info']['firmware_version']):
                            self.flash_firmware_update(device_name,self.recommended[device_name].to_string())
        click.secho('---- Firmware Update Complete!', fg="green",bold=True)
        new_config=CurrrentConfiguration()
        new_config.pretty_print()

    def flash_firmware_update(self,device_name, tag):
        click.secho('-------- FIRMWARE FLASH %s | %s ------------'%(device_name,tag), fg="green", bold=True)
        port_name = Popen("ls -l /dev/" + device_name, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE,close_fds=True).stdout.read().strip().split()[-1]
        if device_name=='hello-motor-left-wheel' or device_name=='hello-motor-right-wheel' or device_name=='hello-motor-arm' or device_name=='hello-motor-lift':
            sketch_name = 'hello_stepper'
        if device_name == 'hello-wacc':
            sketch_name = 'hello_wacc'
        if device_name == 'hello-pimu':
            sketch_name = 'hello_pimu'
        if port_name is not None:
            click.secho('---------------Git Checkout-------------------------', fg="green")
            os.chdir(self.repo.repo_path)
            git_checkout_command='git checkout '+tag
            g = Popen(git_checkout_command, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE,close_fds=True).stdout.read().strip()
            print('Checkout out firmware %s from Git'%tag)
            click.secho('---------------Compile-------------------------', fg="green")
            compile_command = 'arduino-cli compile --fqbn hello-robot:samd:%s %s/arduino/%s'%(sketch_name,self.repo.repo_path,sketch_name)
            print(compile_command)
            c=Popen(compile_command, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip()
            print(c)
            click.secho('---------------Upload-------------------------', fg="green")
            upload_command = 'arduino-cli upload -p /dev/%s --fqbn hello-robot:samd:%s %s/arduino/%s' % (port_name, sketch_name, self.repo.repo_path,sketch_name)
            print(upload_command)
            u = Popen(upload_command, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip()
            print(u)
            return True
        else:
            print('Firmware update %s. Failed to find device %s'%(tag,device_name))
            return False

if args.recommended:
    c = CurrrentConfiguration()
    r = FirmwareRepo()
    u = FirmwareUpdater(c,r)
    u.pretty_print_recommended()
    r.cleanup()

if args.available:
    r=FirmwareRepo()
    r.pretty_print_available_versions()
    r.cleanup()

if args.config:
    c = CurrrentConfiguration()
    c.pretty_print()

if args.update:
    c = CurrrentConfiguration()
    r = FirmwareRepo()
    u = FirmwareUpdater(c, r)
    u.do_update()
    r.cleanup()


if 0:
    port_name=None
    sketch_name=None
    device_name=None

    if args.wacc:
        device_name = 'hello-wacc'
        sketch_name = 'hello_wacc'
        port_name=Popen("ls -l /dev/"+device_name, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip().split()[-1]
        print('Found Wacc at %s'%port_name)
        next_steps="Test the Wacc using: stretch_wacc_jog.py"

    if args.pimu:
        device_name = 'hello-pimu'
        sketch_name = 'hello_pimu'
        port_name=Popen("ls -l /dev/"+device_name, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip().split()[-1]
        print('Found Pimu at %s'%port_name)
        next_steps = "Test the Pimu using: stretch_pimu_jog.py"

    if args.lift:
        device_name = 'hello-motor-lift'
        sketch_name = 'hello_stepper'
        port_name=Popen("ls -l /dev/"+device_name, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip().split()[-1]
        print('Found Lift at %s'%port_name)
        next_steps = "Write the stepper calibration using: RE1_stepper_calibration_YAML_to_flash.py hello-motor-lift"

    if args.arm:
        device_name = 'hello-motor-arm'
        sketch_name = 'hello_stepper'
        port_name=Popen("ls -l /dev/"+device_name, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip().split()[-1]
        print('Found Arm at %s'%port_name)
        next_steps = "Write the stepper calibration using: RE1_stepper_calibration_YAML_to_flash.py hello-motor-arm"

    if args.left_wheel:
        device_name = 'hello-motor-left-wheel'
        sketch_name = 'hello_stepper'
        port_name=Popen("ls -l /dev/"+device_name, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip().split()[-1]
        print('Found Left Wheel at %s'%port_name)
        next_steps = "Write the stepper calibration using: RE1_stepper_calibration_YAML_to_flash.py hello-motor-left-wheel"

    if args.right_wheel:
        device_name = 'hello-motor-right-wheel'
        sketch_name = 'hello_stepper'
        port_name=Popen("ls -l /dev/"+device_name, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip().split()[-1]
        print('Found Right Wheel at %s'%port_name)
        next_steps = "Write the stepper calibration using: RE1_stepper_calibration_YAML_to_flash.py hello-motor-right-wheel"

    if port_name is not None:
        print('Uploading firmware to %s'%sketch_name)
        print('---------------Compile-------------------------')
        compile_command = 'arduino-cli compile --fqbn hello-robot:samd:%s ~/repos/stretch_firmware/arduino/%s'%(sketch_name,sketch_name)
        upload_command = 'arduino-cli upload -p /dev/%s --fqbn hello-robot:samd:%s ~/repos/stretch_firmware/arduino/%s'%(port_name,sketch_name,sketch_name)
        c=Popen(compile_command, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip()
        print(c)
        print('---------------Upload-------------------------')
        u = Popen(upload_command, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip()
        print(u)
        print('---------------Next Steps-------------------------')
        print(next_steps)
    else:
        print 'Failed to upload...'