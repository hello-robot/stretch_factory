#!/usr/bin/env python

import click
import os
from subprocess import Popen, PIPE
import stretch_body.stepper
import stretch_body.pimu
import stretch_body.wacc
import stretch_body.device
import yaml
import time
import sys
import stretch_body.device

import stretch_body.hello_utils
import shlex
from stretch_factory.firmware_available import FirmwareAvailable
from stretch_factory.firmware_recommended import FirmwareRecommended
from stretch_factory.firmware_installed import FirmwareInstalled
from stretch_factory.firmware_version import FirmwareVersion
from stretch_factory.firmware_utils import *

class FirmwareUpdater():
    def __init__(self, use_device):
        self.use_device = use_device
        self.fw_installed = FirmwareInstalled(use_device)
        for device_name in self.use_device.keys():
            self.use_device[device_name] = self.use_device[device_name] and self.fw_installed.is_device_valid(device_name)
        self.fw_available = FirmwareAvailable(use_device)
        self.fw_recommended = FirmwareRecommended(use_device, self.fw_installed, self.fw_available)
        self.target = self.fw_recommended.recommended.copy()


    def startup(self):
        # if not self.__check_ubuntu_version():
        #    print('Firmware Updater does not work on Ubuntu 20.04 currently. Please try again in Ubuntu 18.04')
        #   return False
        if self.__check_arduino_cli_install():
            self.__create_arduino_config_file()
            return True
        return False

# ########################################################################################################3
    def get_update_to(self):
        #Override self.target with user input
        click.secho(' Select target firmware versions '.center(60, '#'), fg="cyan", bold=True)
        for device_name in self.fw_recommended.recommended:
            if self.use_device[device_name]:
                vs = self.fw_available.versions[device_name]
                if len(vs) and self.fw_recommended.recommended[device_name] is not None:
                    print('')
                    click.secho('---------- %s [%s]-----------' % (
                        device_name.upper(), str(self.fw_installed.get_version(device_name))), fg="blue",
                                bold=True)
                    default_id = 0
                    for i in range(len(vs)):
                        if vs[i] == self.fw_recommended.recommended[device_name]:
                            default_id = i
                        print('%d: %s' % (i, vs[i]))
                    print('----------------------')
                    vt = None
                    while vt == None:
                        id = click.prompt('Please enter desired version id [Recommended]', default=default_id)
                        if id >= 0 and id < len(vs):
                            vt = vs[id]
                        else:
                            click.secho('Invalid ID', fg="red")
                    print('Selected version %s for device %s' % (vt, device_name))
                    self.target[device_name] = vt
        print('')
        print('')

    def get_update_to_path(self, path_name):
        # Burn the Head of the branch to each board regardless of what is currently installed
        click.secho('>>> Flashing firmware from path %s ' % path_name, fg="cyan", bold=True)
        # Check that version of target path is compatible
        for device_name in self.target:
            if self.use_device[device_name]:
                sketch_name = self.get_sketch_name(device_name)
                target_version = self.get_firmware_version_from_path(sketch_name, path_name)
                if target_version is None:
                    return False
                self.target[device_name] = target_version
                path_protocol = 'p' + str(target_version.protocol)
                if not self.fw_installed.is_protocol_supported(device_name, path_protocol):
                    click.secho('---------------------------', fg="yellow")
                    click.secho(
                        'Target firmware path of %s is incompatible with installed Stretch Body for device %s' % (
                        path_name, device_name), fg="yellow")
                    x = " , ".join(["{}"] * len(self.fw_installed.get_supported_protocols(device_name))).format(
                        *self.fw_installed.get_supported_protocols(device_name))
                    click.secho('Installed Stretch Body supports protocols %s' % x, fg="yellow")
                    click.secho('Target path supports protocol %s' % path_protocol, fg="yellow")
                    if path_protocol > self.fw_installed.max_protocol_supported(device_name):
                        click.secho('Upgrade Stretch Body first...', fg="yellow")
                    else:
                        click.secho('Downgrade Stretch Body first...', fg="yellow")
                    return False
        self.repo_path = path_name[:path_name.rfind('arduino')]
        return True

    # ########################################################################################################3
    def run(self,args):
        #First construct the updater state dictionary
        self.update_state = self.load_update_state()
        if args.do_resume and not self.update_state:
            click.secho('WARNING: A previous firmware update is not available. Unable to resume', fg="yellow",bold=True)
            return False

        if self.update_state and not args.do_resume:
            click.secho('WARNING: A previous firmware update is incomplete', fg="yellow", bold=True)
            click.secho('WARNING: Run REx_firmware_udpater.py --resume', fg="yellow", bold=True)
            click.secho('WARNING: Or delete file /tmp/firmware_updater_state.yaml and try again.', fg="yellow",bold=True)
            return False

        if not self.update_state: #Starting on a new update
            self.update_state = {}
            self.update_state['verbose'] = args.verbose
            self.update_state['no_prompts'] = args.no_prompts
            self.update_state['verbose'] = args.verbose
            self.update_state['install_version'] = args.install_version

            if args.install_path:
                if args.install_path[0] != '/':
                    self.update_state['install_path']=os.getcwd() + '/' + args.install_path
                else:
                    self.update_state['install_path']=args.install_path
            for device_name in self.target:
                if self.target[device_name] is not None:
                    self.update_state[device_name] = {'flash': False,
                                                      'return_to_bus': False,
                                                      'version_validate':False,
                                                      'calibration_flash': False}


            # if args.install_version:
            #     self.get_update_to()
            #
            # if args.install_path:
            #     self.get_update_to_path(self.update_state['install_path'])

            self.update_state['target'] = self.target.copy()


            # Count how many updates doing
            self.num_update = 0
            for device_name in self.target:
                if self.fw_installed.is_device_valid(device_name) and self.target[device_name] is not None:
                    self.num_update = self.num_update + 1
            self.pretty_print_target()
            if not self.num_update:
                click.secho('System is up to date. No updates to be done', fg="yellow", bold=True)
                return False
            self.print_upload_warning()

        tag = None
        repo_path=None

        self.pretty_print_update_state()

        #Advance the state machine
        if args.no_prompts or click.confirm('Proceed with update??'):
            #update_state is now filled out. Advance the states of all targets

            #Flash all devices
            for d in self.update_state['target']:
                if d is not None and not self.update_state[d]['flash']:
                    self.update_state[d]['flash']=self.do_device_flash(d,tag,repo_path,args.verbose)

            if not self.all_pass('flash'):
                click.secho('WARNING: Not all devices flashed successfully', fg="yellow", bold=True)
                click.secho('WARNING: Reboot machine.', fg="yellow", bold=True)
                click.secho('WARNING: Then run: REx_firmware_udpater.py - -resume')
                return False

            for d in self.update_state['target']:
                if d is not None and not self.update_state[d]['return_to_bus']:
                    self.update_state[d]['return_to_bus']=self.wait_on_return_to_bus(d)

            if not self.all_pass('return_to_bus'):
                click.secho('WARNING: Not all devices returned to bus successfully', fg="yellow", bold=True)
                click.secho('WARNING: Reboot machine.', fg="yellow", bold=True)
                click.secho('WARNING: Then run: REx_firmware_udpater.py - -resume')
                return False

            for d in self.update_state['target']:
                if d is not None and not self.update_state[d]['version_validate']:
                    self.update_state[d]['version_validate'] = self.verify_firmware_version(d)

            if not self.all_pass('verify_firmware_version'):
                click.secho('WARNING: Not all devices have updated to target firmware version', fg="yellow", bold=True)
                click.secho('WARNING: Reboot machine.', fg="yellow", bold=True)
                click.secho('WARNING: Then run: REx_firmware_udpater.py - -resume')
                return False

            for d in self.update_state['target']:
                if d is not None and not self.update_state[d]['calibration_flash']:
                    self.update_state[d]['calibration_flash'] = self.calibration_flash(d)


            if 1:#all_success:
                print('')
                click.secho('----------------- Congratulations! ---------------.', fg="green", bold=True)
                click.secho('No issues encountered. Firmware update successful.', fg="green", bold=True)

    def pretty_print_update_state(self):
        pass

    def all_pass(self,state_name):
        all_pass=True
        for d in self.update_state['target']:
            if d is not None:
                all_pass=all_pass and self.update_state[d][state_name]

# ########################################################################################################################
    def wait_on_return_to_bus(self,device_name):
        click.secho('Checking that device %s returned to bus '%device_name)
        print('It may take several minutes to appear on the USB bus.' )
        ts = time.time()
        found = False
        for i in range(30):
            if not self.wait_on_device(device_name, timeout=10.0):
                print('Trying again: %d\n' % i)
                # Bit of a hack.Sometimes after a firmware flash the device
                # Doesn't fully present on the USB bus with a serial No for Udev to find
                # In does present as an 'Arduino Zero' product. This will attempt to reset it
                # and re-present to the bus
                # time.sleep(1.0)
                # os.system('usbreset \"Arduino Zero\"')
                # time.sleep(1.0)
                print('')
            else:
                found = True
                break
        if not found:
            click.secho('Device %s failed to return to bus after %f seconds.' % (device_name, time.time() - ts),fg="yellow", bold=True)
            return False
        else:
            click.secho('Device %s returned to bus after %f seconds.' % (device_name, time.time() - ts),fg="green", bold=True)
        return True

# ########################################################################################################################
#     def foo(self):
#         all_success = all_success and self.verify_firmware_version(device_name)
#         print('')
#         print('')
#                 # NOTE: Move to exceptions and single device flow, can track where in the flow it fails.
#                 self.post_firmware_update(device_name)
#
#                 if len(no_return):
#                     click.secho('Devices did not return to bus. Power cycle robot', fg="yellow", bold=True)
#                     click.secho('Then run stretch_robot_system_check.py to confirm all devices present', fg="yellow",
#                                 bold=True)
#                     for device_name in no_stepper_return:
#                         click.secho(
#                             'Device %s requires calibration data to be written after power cycle.' % device_name,
#                             fg="yellow", bold=True)
#                         click.secho('After power cycle run: REx_stepper_calibration_YAML_to_flash.py %s' % device_name,
#                                     fg="yellow", bold=True)
#                     return False
#
#                 return all_success
#         return True

# ########################################################################################################################
    def do_device_flash(self,device_name, tag,repo_path=None,verbose=False):
        click.secho('-------- FIRMWARE FLASH %s | %s ------------'%(device_name,tag), fg="cyan", bold=True)
        config_file = self.fw_available.repo_path + '/arduino-cli.yaml'

        user_msg_log('Config: '+str(config_file), user_display=verbose)
        user_msg_log('Repo: '+str(repo_path), user_display=verbose)

        sketch_name=None
        if device_name == 'hello-motor-left-wheel' or device_name == 'hello-motor-right-wheel' or device_name == 'hello-motor-arm' or device_name == 'hello-motor-lift':
            sketch_name = 'hello_stepper'
        if device_name == 'hello-wacc':
            sketch_name = 'hello_wacc'
        if device_name == 'hello-pimu':
            sketch_name = 'hello_pimu'

        if sketch_name=='hello_stepper' and not self.does_stepper_have_encoder_calibration_YAML(device_name):
            print('Encoder data has not been stored for %s and may be lost. Aborting firmware flash.'%device_name)
            return False

        print('Looking for device %s on bus' % device_name)
        if not self.wait_on_device(device_name, timeout=5.0):
            print('Failure: Device not on bus.')
            return False
        port_name = self.get_port_name(device_name)
        user_msg_log('Device: %s Port: %s'%(device_name,port_name), user_display=verbose)
        if port_name is not None and sketch_name is not None:

            print('Starting programming. This will take about 5s...')
            if repo_path is None:
                os.chdir(self.fw_available.repo_path)
                os.system('git checkout '+tag+'>/dev/null 2>&1')
                src_path=self.fw_available.repo_path
            else:
                src_path=repo_path

            compile_command = 'arduino-cli compile --config-file %s --fqbn hello-robot:samd:%s %s/arduino/%s'%(config_file,sketch_name,src_path,sketch_name)
            user_msg_log(compile_command,user_display=verbose)
            c=Popen(shlex.split(compile_command), shell=False, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip()
            if type(c)==bytes:
                c=c.decode("utf-8")
            cc = c.split('\n')
            user_msg_log(c, user_display=verbose)

            # In version 0.18.x the last line after compile is: Sketch uses xxx bytes (58%) of program storage space. Maximum is yyy bytes.
            #In version 0.24.x +this is now on line 0.
            #Need a more robust way to determine successful compile. Works for now.
            self.update_state[device_name]['compile']=(str(cc[0]).find('Sketch uses')!=-1)
            if not self.update_state[device_name]['compile']:
                print('Firmware failed to compile %s at %s' % (sketch_name,src_path))
                return False
            else:
                print('Success in firmware compile')


            upload_command = 'arduino-cli upload  --config-file %s -p /dev/%s --fqbn hello-robot:samd:%s %s/arduino/%s' % (config_file, port_name, sketch_name, src_path,sketch_name)

            user_msg_log(upload_command,user_display=verbose)
            u = Popen(shlex.split(upload_command), shell=False, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip()


            if type(u) == bytes:
                u=u.decode('utf-8')
            uu = u.split('\n')
            user_msg_log(u, user_display=False)
            if verbose:
                print(upload_command)
                # Pretty print the result
                for l in uu:
                    k = l.split('\r')
                    if len(k) == 1:
                        print(k[0])
                    else:
                        for m in k:
                            print(m)
            success = uu[-1] == 'CPU reset.'

            if not success:
                print('Firmware flash. Failed to upload to %s' % (port_name))
                return False
            else:
                print('Success in firmware flash.')
                return True
        else:
            print('Firmware update %s. Failed to find device %s'%(tag,device_name))
            return False

    def save_update_state(self):
        yaml.dump(self.update_state, '/tmp/firmware_updater_state.yaml', default_flow_style=False)
    
    def load_update_state(self):
        #Return dict of update in process, None if none available
        try:
            with open('/tmp/firmware_updater_state.yaml', 'r') as s:
                return yaml.load(s, Loader=yaml.FullLoader)
        except IOError:
            return None

    def __create_arduino_config_file(self):
        arduino_config = {'board_manager': {'additional_urls': []},
                          'daemon': {'port': '50051'},
                          'directories': {'data': os.environ['HOME'] + '/.arduino15',
                                          'downloads': os.environ['HOME'] + '/.arduino15/staging',
                                          'user': self.fw_available.repo_path + '/arduino'},
                          'library': {'enable_unsafe_install': False},
                          'logging': {'file': '', 'format': 'text', 'level': 'info'},
                          'metrics': {'addr': ':9090', 'enabled': True},
                          'sketch': {'always_export_binaries': False},
                          'telemetry': {'addr': ':9090', 'enabled': True}}
        with open(self.fw_available.repo_path + '/arduino-cli.yaml', 'w') as yaml_file:
            yaml.dump(arduino_config, yaml_file, default_flow_style=False)

    def pretty_print_target(self):
        click.secho(' UPDATING FIRMWARE TO... '.center(110, '#'), fg="cyan", bold=True)
        for device_name in self.target:
            if self.use_device[device_name]:
                if not self.fw_installed.is_device_valid(device_name):
                    print('%s | No target available' % device_name.upper().ljust(25))
                else:
                    v_curr = self.fw_installed.get_version(device_name)
                    v_targ = self.target[device_name]
                    if v_targ is None:
                        rec = 'No target available'
                    elif v_curr > v_targ:
                        rec = 'Downgrading to %s' % self.target[device_name]
                    elif v_curr < v_targ:
                        rec = 'Upgrading to %s' % self.target[device_name]
                    else:
                        rec = 'Reinstalling %s' % self.target[device_name]
                    print('%s | %s ' % (device_name.upper().ljust(25), rec.ljust(40)))

    def print_upload_warning(self):
        click.secho('------------------------------------------------', fg="yellow", bold=True)
        click.secho('WARNING: (1) Updating robot firmware should only be done by experienced users', fg="yellow",
                    bold=True)
        click.secho('WARNING: (2) Do not have other robot processes running during update', fg="yellow", bold=True)
        click.secho('WARNING: (3) Leave robot powered on during update', fg="yellow", bold=True)
        if self.use_device['hello-motor-lift']:
            click.secho('WARNING: (4) Ensure Lift has support clamp in place', fg="yellow", bold=True)
            click.secho('WARNING: (5) Lift may make a loud noise during programming. This is normal.', fg="yellow",
                        bold=True)
        click.secho('------------------------------------------------', fg="yellow", bold=True)


    def flash_stepper_calibration(self, device_name):
        if device_name == 'hello-motor-arm' or device_name == 'hello-motor-lift' or device_name == 'hello-motor-right-wheel' or device_name == 'hello-motor-left-wheel':
            click.secho(' Flashing Stepper Calibration: %s '.center(110, '#') % device_name, fg="cyan", bold=True)
            if not self.wait_on_device(device_name):
                click.secho('Device %s failed to return to bus. Power cycle may be required.' % device_name, fg="red", bold=True)
                return False
            #time.sleep(1.0)
            motor = stretch_body.stepper.Stepper('/dev/' + device_name)
            motor.startup()
            if not motor.hw_valid:
                click.secho('Failed to startup stepper %s' % device_name, fg="red", bold=True)
                return False
            else:
                print('Writing gains to flash...')
                motor.write_gains_to_flash()
                motor.push_command()
                print('Gains written to flash')
                print('')
                print('Reading calibration data from YAML...')
                data = motor.read_encoder_calibration_from_YAML()
                print('Writing calibration data to flash...')
                motor.write_encoder_calibration_to_flash(data)
                print('Successful write of FLASH.')
                self.wait_on_device(device_name)
                motor.board_reset()
                motor.push_command()
                motor.transport.ser.close()
                time.sleep(2.0)
                self.wait_on_device(device_name)
                print('Successful return of device to bus.')
        return True

    def do_update_to_branch(self, verbose=False, no_prompts=False):
        # Return True if system was upgraded
        # Return False if system was not upgraded / error happened
        click.secho(' Select target branch '.center(60, '#'), fg="cyan", bold=True)
        branches = self.fw_available.get_remote_branches()
        for id in range(len(branches)):
            print('%d: %s' % (id, branches[id]))
        print('')
        branch_name = None
        while branch_name == None:
            try:
                id = click.prompt('Please enter desired branch id', default=0)
            except click.exceptions.Abort:
                return False
            if id >= 0 and id < len(branches):
                branch_name = branches[id]
            else:
                click.secho('Invalid ID', fg="red")
        print('Selected branch %s' % branch_name)
        # Check that version of target branch is compatible
        for device_name in self.target:
            if self.use_device[device_name]:
                sketch_name = self.get_sketch_name(device_name)
                target_version = self.get_firmware_version_from_git(sketch_name, branch_name)
                self.target[device_name] = target_version
                git_protocol = 'p' + str(target_version.protocol)
                if not self.fw_installed.is_protocol_supported(device_name, git_protocol):
                    click.secho('---------------------------', fg="yellow")
                    click.secho(
                        'Target firmware branch of %s is incompatible with installed Stretch Body for device %s' % (
                        branch_name, device_name), fg="yellow")
                    x = " , ".join(["{}"] * len(self.fw_installed.get_supported_protocols(device_name))).format(
                        *self.fw_installed.get_supported_protocols(device_name))
                    click.secho('Installed Stretch Body supports protocols %s' % x, fg="yellow")
                    click.secho('Target branch supports protocol %s' % git_protocol, fg="yellow")
                    if git_protocol > self.fw_installed.max_protocol_supported(device_name):
                        click.secho('Upgrade Stretch Body first...', fg="yellow")
                    else:
                        click.secho('Downgrade Stretch Body first...', fg="yellow")
                    return False
        return self.do_update(verbose=verbose, no_prompts=no_prompts)

    def verify_firmware_version(self,device_name):
        fw_installed = FirmwareInstalled({device_name: True})  # Pull the currently installed system from fw
        if not fw_installed.is_device_valid(device_name):  # Device may not have come back on bus
            print('%s | No device available' % device_name.upper().ljust(25))
            print('')
            return False
        else:
            click.secho(' Confirming Firmware Updates '.center(110, '#'), fg="cyan", bold=True)
            v_curr = fw_installed.get_version(device_name)  # Version that is now on the board
            if v_curr == self.target[device_name]:
                click.secho('%s | %s ' % (device_name.upper().ljust(25), 'Installed firmware matches target'.ljust(40)),fg="green")
                return True
            else:
                click.secho('%s | %s ' % (device_name.upper().ljust(25), 'Firmware update failure!!'.ljust(40)),fg="red", bold=True)
                return False

    def get_firmware_version_from_path(self,sketch_name,path):
        file_path = path+'/'+sketch_name+'/Common.h'
        try:
            f=open(file_path,'r')
        except IOError:
            click.secho('Invalid path provided. Path should should have sketch directories under it',fg="red", bold=True)
            return None
        lines=f.readlines()
        for l in lines:
            if l.find('FIRMWARE_VERSION')>=0:
                version=l[l.find('"')+1:-2] #Format of: '#define FIRMWARE_VERSION "Wacc.v0.0.1p1"\n'
                return FirmwareVersion(version)
        return None

    def get_firmware_version_from_git(self,sketch_name,tag):
        #click.secho('---------------Git Checkout-------------------------', fg="green")
        os.chdir(self.fw_available.repo_path)
        os.system('git checkout ' + tag +' >/dev/null 2>&1')
        #print('Checked out out firmware %s from Git for %s' % (tag,sketch_name))
        file_path = self.fw_available.repo_path+'/arduino/'+sketch_name+'/Common.h'
        f=open(file_path,'r')
        lines=f.readlines()
        for l in lines:
            if l.find('FIRMWARE_VERSION')>=0:
                version=l[l.find('"')+1:-2] #Format of: '#define FIRMWARE_VERSION "Wacc.v0.0.1p1"\n'
                return FirmwareVersion(version)
        return None

