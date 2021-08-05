#!/usr/bin/env python

import click
import os
from subprocess import Popen, PIPE
import git
import stretch_body.stepper
import stretch_body.pimu
import stretch_body.wacc
import yaml
import time
import sys

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
                    click.echo('Installed Stretch Body requires protocol: %s'%self.config_info[device]['valid_firmware_protocol'])
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
        self.repo_path = '/tmp/stretch_firmware_update'
        if not os.path.isdir(self.repo_path):
            #print('Cloning latest version of Stretch Firmware to %s'% self.repo_path)
            git.Repo.clone_from('https://github.com/hello-robot/stretch_firmware',  self.repo_path)
        self.repo = git.Repo(self.repo_path)
        os.chdir(self.repo_path)
        os.system('git checkout master')
        os.system('git fetch --tags')
        os.system('git pull')


    def pretty_print_available_versions(self):
        click.secho('######### Currently Tagged Versions of Stretch Firmware on Master Branch ##########',fg="green", bold=True)
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
            v = FirmwareVersion(t.name)
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
    def __init__(self,version_str):
        self.device='NONE'
        self.major=0
        self.minor=0
        self.bugfix=0
        self.protocol=0
        self.valid=False
        self.from_string(version_str)
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

    def __ne__(self,other):
        return not self.__eq__(other)

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

    def startup(self):
        if self.__check_arduino_cli_install():
            self.__create_arduino_config_file()
            self.__get_recommend_updates()
            return True
        return False


    def __get_recommend_updates(self):
        for device_name in self.recommended.keys():
            if self.use_device[device_name]:
                    cfg=self.current_config.config_info[device_name] #Dictionary of installed configuration for this device
                    if cfg is not None: #Len 0 if device not found
                        v = self.repo.get_most_recent_version(device_name, cfg['valid_firmware_protocol'])
                        self.recommended[device_name]=v
        self.target=self.recommended.copy()


    def __create_arduino_config_file(self):
        arduino_config = {'board_manager': {'additional_urls': []},
                          'daemon': {'port': '50051'},
                          'directories': {'data': os.environ['HOME'] + '/.arduino15',
                                          'downloads': os.environ['HOME'] + '/.arduino15/staging',
                                          'user': self.repo.repo_path + '/arduino'},
                          'library': {'enable_unsafe_install': False},
                          'logging': {'file': '', 'format': 'text', 'level': 'info'},
                          'metrics': {'addr': ':9090', 'enabled': True},
                          'sketch': {'always_export_binaries': False},
                          'telemetry': {'addr': ':9090', 'enabled': True}}
        with open(self.repo.repo_path + '/arduino-cli.yaml', 'w') as yaml_file:
            yaml.dump(arduino_config, yaml_file, default_flow_style=False)

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



    def do_update(self,no_prompts=False):
        # Return True if system was upgraded
        # Return False if system was not upgraded / error happened
        self.num_update=0
        for device_name in self.target.keys():
            if self.use_device[device_name] and self.current_config.config_info[device_name] and self.target[device_name] is not None:
                if not (self.target[device_name].to_string() == self.current_config.config_info[device_name]['board_info']['firmware_version']):
                    self.num_update=self.num_update+1
        self.pretty_print_target()
        if not self.num_update:
            click.secho('System is up to date. No updates to be done', fg="yellow",bold=True)
            return False
        self.print_upload_warning()
        self.fw_updated={}
        if no_prompts or click.confirm('Proceed with update??'):
            for device_name in self.target.keys():
                self.fw_updated[device_name]=False
                if self.use_device[device_name]:
                    if self.target[device_name] is not None:
                        if not (self.target[device_name].to_string()==self.current_config.config_info[device_name]['board_info']['firmware_version']):
                            self.fw_updated[device_name]=self.flash_firmware_update(device_name,self.target[device_name].to_string())
            click.secho('---- Firmware Update Complete!', fg="green",bold=True)
            success=self.post_firmware_update()
            return success

    def do_update_to(self):
        # Return True if system was upgraded
        # Return False if system was not upgraded / error happened
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
        return self.do_update()

    def do_update_to_branch(self):
        # Return True if system was upgraded
        # Return False if system was not upgraded / error happened
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

        #Check that version of target branch is compatible
        for device_name in self.target.keys():
            if self.use_device[device_name]:
                sketch_name=self.get_sketch_name(device_name)
                git_protocol = self.get_firmware_version_from_git(sketch_name, branch_name).protocol
                body_protocol = int(self.current_config.config_info[device_name]['valid_firmware_protocol'][1:])
                if git_protocol!=body_protocol:
                    click.secho('---------------------------', fg="yellow")
                    click.secho('Target firmware branch of %s is incompatible with installed Stretch Body for device %s'%(branch_name,device_name),fg="yellow")
                    click.secho('Installed Stretch Body supports protocol P%d'%body_protocol,fg="yellow")
                    click.secho('Target branch supports protocol P%d'%git_protocol,fg="yellow")
                    if git_protocol>body_protocol:
                        click.secho('Upgrade Stretch Body first...',fg="yellow")
                    else:
                        click.secho('Downgrade Stretch Body first...',fg="yellow")
                    return False
        #Burn the Head of the branch to each board regardless of what is currently installed
        click.secho('############## Updating to branch %s <HEAD> ##############'%branch_name.upper(), fg="green", bold=True)
        self.print_upload_warning()
        self.fw_updated = {}
        if click.confirm('Proceed with update??'):
            for device_name in self.target.keys():
                self.fw_updated[device_name] = False
                if self.use_device[device_name] and self.current_config.config_info[device_name]:
                    self.fw_updated[device_name] = self.flash_firmware_update(device_name, branch_name)
            click.secho('---- Firmware Update Complete!', fg="green", bold=True)
            return self.post_firmware_update(from_branch=True)
        return False

    def flash_stepper_calibration(self,device_name):
        if device_name == 'hello-motor-arm' or device_name == 'hello-motor-lift' or device_name == 'hello-motor-right-wheel' or device_name == 'hello-motor-left-wheel':
                click.secho('############## Flashing Stepper Calibration: %s ##############' % device_name, fg="green",bold=True)
                time.sleep(1.0)
                motor = stretch_body.stepper.Stepper('/dev/' + device_name)
                motor.startup()
                if not motor.hw_valid:
                    click.secho('Failed to startup stepper %s' % device_name, fg="red", bold=True)
                else:
                    print('Reading calibration data from YAML...')
                    data = motor.read_encoder_calibration_from_YAML()
                    print('Writing calibration data to flash...')
                    motor.write_encoder_calibration_to_flash(data)
                    print('Successful write of FLASH. Resetting board now.')
                    motor.board_reset()
                    motor.push_command()
                    motor.transport.ser.close()
                    time.sleep(2.0)
                    self.wait_on_device(device_name)



    def post_firmware_update(self,from_branch=False):
        #Return True if no errors
        for device_name in self.target.keys():
            if self.fw_updated[device_name]:
                self.flash_stepper_calibration(device_name)
        print('')
        click.secho('############## Confirming Firmware Updates ##############', fg="green", bold=True)
        self.current_config = CurrrentConfiguration(self.use_device)
        success=True
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
                        success=False
        return success


    def get_firmware_version_from_git(self,sketch_name,tag):
        #click.secho('---------------Git Checkout-------------------------', fg="green")
        os.chdir(self.repo.repo_path)
        git_checkout_command = 'git checkout ' + tag
        g = Popen(git_checkout_command, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE,
                  close_fds=True).stdout.read().strip()
        print('Checkout out firmware %s from Git for %s' % (tag,sketch_name))
        file_path = self.repo.repo_path+'/arduino/'+sketch_name+'/Common.h'
        f=open(file_path,'r')
        lines=f.readlines()
        for l in lines:
            if l.find('FIRMWARE_VERSION')>=0:
                version=l[l.find('"')+1:-2] #Format of: '#define FIRMWARE_VERSION "Wacc.v0.0.1p1"\n'
                return FirmwareVersion(version)
        return None

    def get_sketch_name(self,device_name):
        if device_name=='hello-motor-left-wheel' or device_name=='hello-motor-right-wheel' or device_name=='hello-motor-arm' or device_name=='hello-motor-lift':
            return 'hello_stepper'
        if device_name == 'hello-wacc':
            return 'hello_wacc'
        if device_name == 'hello-pimu':
            return 'hello_pimu'

    def exec_process(self,cmdline, silent, input=None, **kwargs):
        """Execute a subprocess and returns the returncode, stdout buffer and stderr buffer.
           Optionally prints stdout and stderr while running."""
        try:
            sub = Popen(cmdline, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                                   **kwargs)
            stdout, stderr = sub.communicate(input=input)
            returncode = sub.returncode
            if not silent:
                sys.stdout.write(stdout.decode('utf-8'))
                sys.stderr.write(stderr.decode('utf-8'))
        except OSError as e:
            if e.errno == 2:
                raise RuntimeError('"%s" is not present on this system' % cmdline[0])
            else:
                raise
        if returncode != 0:
            raise RuntimeError('Got return value %d while executing "%s", stderr output was:\n%s' % (
            returncode, " ".join(cmdline), stderr.rstrip(b"\n")))
        return stdout

    # ###################################
    def is_device_present(self,device_name):
        try:
            self.exec_process(['ls', '/dev/'+device_name], True)
            return True
        except RuntimeError as e:
            return False

    def wait_on_device(self,device_name,timeout=10.0):
        #Wait for device to appear on bus for timeout seconds
        print('Waiting for device %s to return to bus.'%device_name)
        ts=time.time()
        itr=0
        while(time.time()-ts<timeout):
            if self.is_device_present(device_name):
                print('\n')
                return True
            itr=itr+1
            if itr % 5 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()
            time.sleep(0.1)
        print('\n')
        return False

    def get_port_name(self, device_name):
        try:
            port_name = Popen("ls -l /dev/" + device_name, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE,close_fds=True).stdout.read().strip().split()[-1]
            if not type(port_name)==str:
                port_name=port_name.decode('utf-8')
            return port_name
        except IndexError:
            return None

    def flash_firmware_update(self,device_name, tag):
        click.secho('-------- FIRMWARE FLASH %s | %s ------------'%(device_name,tag), fg="green", bold=True)
        config_file = self.repo.repo_path + '/arduino-cli.yaml'
        if device_name == 'hello-motor-left-wheel' or device_name == 'hello-motor-right-wheel' or device_name == 'hello-motor-arm' or device_name == 'hello-motor-lift':
            sketch_name = 'hello_stepper'
        if device_name == 'hello-wacc':
            sketch_name = 'hello_wacc'
        if device_name == 'hello-pimu':
            sketch_name = 'hello_pimu'
        port_name = self.get_port_name(device_name)
        if port_name is not None:
            click.secho('---------------Git Checkout-------------------------', fg="green")
            os.chdir(self.repo.repo_path)
            git_checkout_command='git checkout '+tag
            g = Popen(git_checkout_command, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE,close_fds=True).stdout.read().strip()
            print('Checkout out firmware %s from Git'%tag)
            click.secho('---------------Compile-------------------------', fg="green")
            compile_command = 'arduino-cli compile --config-file %s --fqbn hello-robot:samd:%s %s/arduino/%s'%(config_file,sketch_name,self.repo.repo_path,sketch_name)
            print(compile_command)
            c=Popen(compile_command, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip()
            print(c)
            click.secho('---------------Upload-------------------------', fg="green")
            upload_command = 'arduino-cli upload --config-file %s -p /dev/%s --fqbn hello-robot:samd:%s %s/arduino/%s' % (config_file, port_name, sketch_name, self.repo.repo_path,sketch_name)
            print(upload_command)
            u = Popen(upload_command, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip()
            uu = u.split(b'\n')
            # Pretty print the result
            for l in uu:
                k = l.split(b'\r')
                if len(k) == 1:
                    print(k[0].decode('utf-8'))
                else:
                    for m in k:
                        print(m.decode('utf-8'))
            success = uu[-1] == b'CPU reset.'
            if not success:
                print('Firmware flash. Failed to upload to %s' % (port_name))
            else:
                print('Success in firmware flash.')
                if self.wait_on_device(device_name):
                    return True
            print('Failure for device %s to return to USB bus after upload'%device_name)
            return False
        else:
            print('Firmware update %s. Failed to find device %s'%(tag,device_name))
            return False
