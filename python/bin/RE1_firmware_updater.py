#!/usr/bin/env python
import argparse
import click
import os
from subprocess import Popen, PIPE
import git

import stretch_body.stepper
import stretch_body.pimu
import stretch_body.wacc
import stretch_body.hello_utils as hu

parser=argparse.ArgumentParser(description='Upload Stretch firmware to microcontrollers')

group = parser.add_mutually_exclusive_group()
parser.add_argument("--status", help="Display the current firmware status",action="store_true")
group.add_argument("--update", help="Update to recommended firmware",action="store_true")
group.add_argument("--update_to", help="Update to a specific firmware version",action="store_true")
group.add_argument("--update_to_branch", help="Update to HEAD of a specific branch",action="store_true")
group.add_argument("--mgmt", help="Display overview on firmware management",action="store_true")

parser.add_argument("--pimu", help="Upload Pimu firmware",action="store_true")
parser.add_argument("--wacc", help="Upload Wacc firmware",action="store_true")
parser.add_argument("--arm", help="Upload Arm Stepper firmware",action="store_true")
parser.add_argument("--lift", help="Upload Lift Stepper firmware",action="store_true")
parser.add_argument("--left_wheel", help="Upload Left Wheel Stepper firmware",action="store_true")
parser.add_argument("--right_wheel", help="Upload Right Wheel Stepper firmware",action="store_true")


args=parser.parse_args()

mgmt="""
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

class CurrrentConfiguration():
    def __init__(self,use_device):
        self.use_device=use_device
        self.config_info={'hello-motor-lift': {},'hello-motor-arm':{},'hello-motor-left-wheel':{},'hello-motor-right-wheel':{},'hello-pimu':{},'hello-wacc':{}}
        for device in self.config_info.keys():
            if self.use_device[device]:
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
                else:
                    self.config_info[device]=None

    def pretty_print(self):
        click.secho('############## Currently Installed Configuration ##############',fg="green", bold=True)
        for device in self.config_info:
            if self.use_device[device]:
                click.secho('------------ %s ------------'%device.upper())
                if self.config_info[device]:
                    click.echo('Installed Firmware: %s'%self.config_info[device]['board_info']['firmware_version'])
                    click.echo('Stretch Body requires protocol: %s'%self.config_info[device]['valid_firmware_protocol'])
                    if self.config_info[device]['protocol_match']:
                        click.secho('Protocol match',fg="green")
                    else:
                        click.secho('Protocol mismatch',fg="yellow")
                else:
                    click.secho('Device not found')

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
        click.secho('######### Currently Available Versions of Stretch Firmware on GitHub ##########',fg="green", bold=True)
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

    def get_remote_branches(self):
        branches=[]
        for ref in self.repo.git.branch('-r').split('\n'):
            branches.append(ref)
        return branches




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
        if not self.valid or not other.valid:
            return False
        if self.protocol>other.protocol:
            return True
        if self.major > other.major:
            return True
        if self.minor > other.minor:
            return True
        if self.bugfix > other.bugfix:
            return True
        return False

    def __lt__(self, other):
        if not self.valid or not other.valid:
            return False
        if self.protocol<other.protocol:
            return True
        if self.major < other.major:
            return True
        if self.minor < other.minor:
            return True
        if self.bugfix < other.bugfix:
            return True
        return False
    def __eq__(self,other):
        if not other or not self.valid or not other.valid:
            return False
        return self.major == other.major and self.minor == other.minor and self.bugfix == other.bugfix and self.protocol==other.protocol

    def same_device(self,d):
        return d==self.device
    def same_protocol(self,p):
        return p==self.protocol

    def from_string(self,x):
        #X is of form 'Stepper.v0.0.1p0'
        try:
            xl=x.split('.')
            if len(xl) != 4:
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
    def __init__(self,use_device,current_config,repo):
        self.use_device=use_device
        self.repo=repo
        self.current_config=current_config
        self.recommended = {'hello-motor-lift': None, 'hello-motor-arm': None, 'hello-motor-left-wheel': None,'hello-motor-right-wheel': None, 'hello-pimu': None, 'hello-wacc': None}
        if self.__check_arduino_cli_install():
            self.__get_recommend_updates()
        else:
            exit()


    def __get_recommend_updates(self):
        for device_name in self.recommended.keys():
            if self.use_device[device_name]:
                    cfg=self.current_config.config_info[device_name] #Dictionary of installed configuration for this device
                    if cfg is not None: #Len 0 if device not found
                        v = self.repo.get_most_recent_version(device_name, cfg['valid_firmware_protocol'])
                        self.recommended[device_name]=v
        self.target=self.recommended.copy()

    def __check_arduino_cli_install(self):
        res=Popen('arduino-cli version', shell=True, bufsize=64, stdin=PIPE, stdout=PIPE,close_fds=True).stdout.read()[:11]
        if not(res==b'arduino-cli'):
            click.secho('WARNING:---------------------------------------------------------------------------------', fg="yellow", bold=True)
            click.secho('WARNING: Tool arduino_cli not installed. See stretch_install_dev.sh (Stretch Install repo)', fg="yellow", bold=True)
            click.secho('WARNING:---------------------------------------------------------------------------------', fg="yellow", bold=True)
            print('')
            return False
        return True

    def pretty_print_recommended(self):
        click.secho('############## Recommended Firmware Updates ##############', fg="green",bold=True)
        for device_name in self.recommended.keys():
            if self.use_device[device_name] :
                if self.current_config.config_info[device_name] is None:
                    print('%s | No device available'%device_name.upper().ljust(25))
                else:
                    cfg = self.current_config.config_info[device_name]
                    if self.recommended[device_name]==None:
                        print('%s | No recommendations available (might be on dev branch)' % device_name.upper().ljust(25))
                    else:
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
                        print('%s | %s ' % (device_name.upper().ljust(25), rec.ljust(40)))

    def pretty_print_target(self):
        click.secho('############## Targeted Firmware Updates ##############', fg="green", bold=True)
        for device_name in self.target.keys():
            if self.use_device[device_name]:
                if self.current_config.config_info[device_name] is None:
                    print('%s | No target available' % device_name.upper().ljust(25))
                else:
                    cfg = self.current_config.config_info[device_name]
                    v_curr=FirmwareVersion(cfg['board_info']['firmware_version'])
                    v_targ=self.target[device_name]
                    if v_targ is None:
                        rec = 'No target available'
                    elif v_curr > v_targ:
                        rec = 'Downgrading to %s' % self.target[device_name]
                    elif v_curr<v_targ:
                        rec = 'Upgrading to %s' % self.target[device_name]
                    else:
                        rec = 'Already at target of %s' % self.target[device_name]
                    print('%s | %s ' % (device_name.upper().ljust(25), rec.ljust(40)))

    def print_upload_warning(self):
        click.secho('------------------------------------------------', fg="yellow", bold=True)
        click.secho('WARNING: Updating robot firmware should only be done by experienced users', fg="yellow", bold=True)
        click.secho('WARNING: Do not have other robot processes running during update', fg="yellow", bold=True)
        click.secho('WARNING: Leave robot powered on during update', fg="yellow", bold=True)
        click.secho('WARNING: Ensure Lift has support clamp in place', fg="yellow", bold=True)
        click.secho('------------------------------------------------', fg="yellow", bold=True)

    def do_update(self):
        #Count number of updates to do
        self.num_update=0
        for device_name in self.target.keys():
            if self.use_device[device_name] and self.current_config.config_info[device_name] and self.target[device_name] is not None:
                if not (self.target[device_name].to_string() == self.current_config.config_info[device_name]['board_info']['firmware_version']):
                    self.num_update=self.num_update+1
        self.pretty_print_target()
        if not self.num_update:
            click.secho('System is up to date. No updates to be done', fg="yellow",bold=True)
            return
        self.print_upload_warning()
        self.fw_updated={}
        if click.confirm('Proceed with update??'):
            for device_name in self.target.keys():
                self.fw_updated[device_name]=False
                if self.use_device[device_name]:
                    if self.target[device_name] is not None:
                        if not (self.target[device_name].to_string()==self.current_config.config_info[device_name]['board_info']['firmware_version']):
                            self.flash_firmware_update(device_name,self.target[device_name].to_string())
                            self.fw_updated[device_name]=True
            click.secho('---- Firmware Update Complete!', fg="green",bold=True)
            self.post_firmware_update()

    def do_update_to(self):
        click.secho('######### Selecting target firmware versions ###########', fg="green", bold=True)
        for device_name in self.recommended.keys():
            if self.use_device[device_name]:
                vs=self.repo.versions[device_name]
                if len(vs) and self.recommended[device_name] is not None:
                    print('')
                    click.secho('---------- %s [%s]-----------'%(device_name.upper(),self.current_config.config_info[device_name]['board_info']['firmware_version']), fg="blue", bold=True)
                    default_id=0
                    for i in range(len(vs)):
                        if vs[i]==self.recommended[device_name]:
                            default_id=i
                        print('%d: %s'%(i,vs[i]))
                    print('----------------------')
                    vt=None
                    while vt==None:
                        id = click.prompt('Please enter desired version id [Recommended]', default=default_id)
                        if id>=0 and id<len(vs):
                            vt=vs[id]
                        else:
                            click.secho('Invalid ID', fg="red" )
                    print('Selected version %s for device %s'%(vt,device_name))
                    self.target[device_name]=vt
        print('')
        print('')
        self.do_update()

    def do_update_to_branch(self):
        click.secho('######### Selecting target branch ###########', fg="green", bold=True)
        branches=self.repo.get_remote_branches()
        for id in range(len(branches)):
            print('%d: %s' % (id, branches[id]))
        print('')
        branch_name=None
        while branch_name == None:
            id = click.prompt('Please enter desired branch id',default=0)
            if id >= 0 and id < len(branches):
                branch_name=branches[id]
            else:
                click.secho('Invalid ID', fg="red")
        print('Selected branch %s'%branch_name )
        print('')
        print('')
        #Burn the Head of the branch to each board regardless of what is currently installed
        click.secho('############## Updating to branch %s <HEAD> ##############'%branch_name.upper(), fg="green", bold=True)
        self.print_upload_warning()
        self.fw_updated = {}
        if click.confirm('Proceed with update??'):
            for device_name in self.target.keys():
                self.fw_updated[device_name] = False
                if self.use_device[device_name] and self.current_config.config_info[device_name]:
                    self.flash_firmware_update(device_name, branch_name)
                    self.fw_updated[device_name] = True
            click.secho('---- Firmware Update Complete!', fg="green", bold=True)
            self.post_firmware_update(from_branch=True)

    def post_firmware_update(self,from_branch=False):
        click.secho('############## Resetting USB Bus ##############', fg="green", bold=True)
        os.system('RE1_usb_reset.py')
        self.current_config = CurrrentConfiguration(self.use_device)
        print('')
        click.secho('############## Confirming Firmware Updates ##############', fg="green", bold=True)
        for device_name in self.target.keys():
            if self.use_device[device_name] and self.fw_updated[device_name]:
                if self.current_config.config_info[device_name] is None:
                    print('%s | No device available' % device_name.upper().ljust(25))
                else:
                    cfg = self.current_config.config_info[device_name]
                    v_curr = FirmwareVersion(cfg['board_info']['firmware_version'])
                    if not from_branch:
                        v_targ = self.target[device_name]
                    else:
                        v_targ=v_curr
                    if v_curr == v_targ:
                        click.secho('%s | %s ' % (device_name.upper().ljust(25), 'Installed firmware matches target'.ljust(40)),fg="green")
                    else:
                        click.secho('%s | %s ' % (device_name.upper().ljust(25), 'Firmware update failure!!'.ljust(40)),fg="red", bold=True)
        print('')
        click.secho('############## Flashing Stepper Calibration ##############', fg="green", bold=True)
        for device_name in self.fw_updated.keys():
            if self.fw_updated[device_name]:
                if device_name=='hello-motor-arm' or device_name=='hello-motor-lift' or device_name=='hello-motor-right-wheel' or device_name=='hello-motor-left-wheel':
                    motor = stretch_body.stepper.Stepper('/dev/' + device_name)
                    motor.startup()
                    if not motor.hw_valid:
                        click.secho('Failed to startup stepper %s'%device_name,fg="red", bold=True)
                    else:
                        print('Reading calibration data from YAML...')
                        data = motor.read_encoder_calibration_from_YAML()
                        print('Writing calibration data to flash...')
                        motor.write_encoder_calibration_to_flash(data)
                        print('Successful write of FLASH. Resetting board now.')
                        motor.board_reset()
                        motor.push_command()
        click.secho('############## Resetting USB Bus ##############', fg="green", bold=True)
        os.system('RE1_usb_reset.py')

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
    r.cleanup()
else:
    parser.print_help()

