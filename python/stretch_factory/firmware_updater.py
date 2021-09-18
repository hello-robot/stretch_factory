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


# #####################################################################################################
class FirmwareVersion():
    """
    Manage comparision of firmware versions
    """
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
        """
        Version is represented as Stepper.v0.0.1p0 for example
        """
        return self.device+'.v'+str(self.major)+'.'+str(self.minor)+'.'+str(self.bugfix)+'p'+str(self.protocol)

    def __gt__(self, other):
        if not self.valid or not other.valid:
            return False
        if self.protocol>other.protocol:
            return True
        if self.protocol<other.protocol:
            return False
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
        if self.protocol>other.protocol:
            return False
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
# #####################################################################################################
class InstalledFirmware():
    """
    Pull the current installed firmware off the robot uCs
    Build config_info of form:
    {'hello-motor-arm': {'board_info': {'board_version': u'Stepper.Irma.V1',
       'firmware_version': u'Stepper.v0.0.1p1',
       'protocol_version': u'p1'},
      'installed_protocol_valid': True,
      'supported_protocols': ['p0', 'p1']}}
    """
    def __init__(self,use_device):
        """
        use_device has form of:
        {'hello-motor-lift': True, 'hello-motor-arm': True, 'hello-motor-right-wheel': True, 'hello-motor-left-wheel': True, 'hello-pimu': True, 'hello-wacc': True}
        """
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
                    self.config_info[device]['supported_protocols']=dd.supported_protocols.keys()
                    self.config_info[device]['installed_protocol_valid']=(dd.board_info['protocol_version']in self.config_info[device]['supported_protocols'])
                    self.config_info[device]['version']=FirmwareVersion(self.config_info[device]['board_info']['firmware_version'])
                    dd.stop()
                else:
                    self.config_info[device]=None

    def is_protocol_supported(self,device_name,p):
        """
        Provide 'p0', etc
        """
        return p in self.config_info[device_name]['supported_protocols']

    def max_protocol_supported(self,device_name):
        x=[int(x[1:]) for x in self.config_info[device_name]['supported_protocols']]
        return 'p'+str(max(x))

    def pretty_print(self):
        click.secho('############## Currently Installed Firmware ##############',fg="cyan", bold=True)
        for device in self.config_info:
            if self.use_device[device]:
                click.secho('------------ %s ------------'%device.upper(),fg="white", bold=True)
                if self.config_info[device]:
                    click.echo('Installed Firmware: %s'%self.config_info[device]['board_info']['firmware_version'])
                    x=" , ".join(["{}"]*len(self.config_info[device]['supported_protocols'])).format(*self.config_info[device]['supported_protocols'])
                    click.echo('Installed Stretch Body supports protocols: '+x)
                    if self.config_info[device]['installed_protocol_valid']:
                        click.secho('Installed protocol %s : VALID'%self.config_info[device]['board_info']['protocol_version'])
                    else:
                        click.secho('Installed protocol %s : INVALID'%self.config_info[device]['board_info']['protocol_version'],fg="yellow")
                else:
                    click.secho('Device not found')
# #####################################################################################################
class AvailableFirmware():
    def __init__(self,use_device):
        self.use_device=use_device
        self.repo=None
        self.repo_path=None
        self.versions = {}
        for d in self.use_device:
            if self.use_device[d]:
                self.versions[d]=[] #List of available versions for that device
        self.__clone_firmware_repo()
        self.__get_available_firmware_versions()

    def __clone_firmware_repo(self):
        self.repo_path = '/tmp/stretch_firmware_update'
        if not os.path.isdir(self.repo_path):
            #print('Cloning latest version of Stretch Firmware to %s'% self.repo_path)
            git.Repo.clone_from('https://github.com/hello-robot/stretch_firmware',  self.repo_path)
        self.repo = git.Repo(self.repo_path)
        os.chdir(self.repo_path)
        os.system('git checkout master >/dev/null 2>&1')
        os.system('git fetch --tags >/dev/null 2>&1 ')
        os.system('git pull >/dev/null 2>&1 ')


    def pretty_print(self):
        click.secho('######### Currently Tagged Versions of Stretch Firmware on Master Branch ##########',fg="cyan", bold=True)
        for device_name in self.versions.keys():
            click.secho('---- %s ----'%device_name.upper(), fg="white", bold=True)
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
                for device_name in self.versions:
                    if (v.device == 'Stepper' and device_name in ['hello-motor-lift','hello-motor-arm','hello-motor-left-wheel','hello-motor-right-wheel']) or\
                        (v.device == 'Wacc' and device_name=='hello-wacc') or\
                        (v.device == 'Pimu' and device_name=='hello-pimu'):
                            self.versions[device_name].append(v)



    def get_most_recent_version(self,device_name,supported_protocols):
        """
        For the device and supported protocol versions (eg, '['p0','p1']'), return the most recent version (type FirmwareVersion)
        """
        if len(self.versions[device_name])==0:
            return None
        recent=None
        s=[int(x[1:]) for x in supported_protocols ]
        supported_versions=[]
        for v in self.versions[device_name]:
            if v.protocol in s:
                supported_versions.append(v)
        for sv in supported_versions:
            if recent is None or sv>recent:
                recent=sv
        return recent


    def get_remote_branches(self):
        branches=[]
        for ref in self.repo.git.branch('-r').split('\n'):
            branches.append(ref)
        branches=[b for b in branches if b.find('HEAD')==-1]
        return branches

# #####################################################################################################
class RecommendedFirmware():
    def __init__(self,use_device,installed=None,available=None):
        self.use_device=use_device
        self.fw_installed = InstalledFirmware(use_device) if installed is None else installed
        self.fw_available= AvailableFirmware(use_device) if available is None else available
        self.recommended = {}
        self.__get_recommend_updates()

    def __get_recommend_updates(self):
        for device_name in self.use_device.keys():
            if self.use_device[device_name]:
                    cfg=self.fw_installed.config_info[device_name] #Dictionary of installed configuration for this device
                    if cfg is not None: #Len 0 if device not found
                        self.recommended[device_name]=self.fw_available.get_most_recent_version(device_name, cfg['supported_protocols'])
                    else:
                        self.recommended[device_name]=None
        #self.target=self.recommended.copy()

    def pretty_print(self):
        click.secho('############## Recommended Firmware Updates ##############\n', fg="cyan",bold=True)
        click.secho('%s | %s | %s | %s ' % ('DEVICE'.ljust(25), 'INSTALLED'.ljust(25), 'RECOMMENDED'.ljust(25), 'ACTION'.ljust(25)), fg="cyan", bold=True)
        click.secho('-'*110,fg="cyan", bold=True)
        for device_name in self.recommended.keys():
            dev_out=device_name.upper().ljust(25)
            installed_out=''.ljust(25)
            rec_out = ''.ljust(25)
            action_out = ''.ljust(25)
            if self.fw_installed.config_info[device_name] is None:
                installed_out='No device available'.ljust(25)
            else:
                cfg = self.fw_installed.config_info[device_name]
                installed_out=str(cfg['version']).ljust(25)
                if self.recommended[device_name]==None:
                   rec_out='None (might be on dev branch)'.ljust(25)
                else:
                    rec_out=str(self.recommended[device_name]).ljust(25)
                    if self.recommended[device_name] > cfg['version']:
                        action_out='Upgrade recommended'.ljust(25)
                    elif self.recommended[device_name] < cfg['version']:
                        action_out='Downgrade recommended'.ljust(25)
                    else:
                        action_out = 'At most recent version'.ljust(25)
            print('%s | %s | %s | %s ' %(dev_out,installed_out,rec_out,action_out))
# #####################################################################################################
class FirmwareUpdater():
    def __init__(self,use_device):
        self.use_device=use_device
        self.fw_installed = InstalledFirmware(use_device)
        self.fw_available= AvailableFirmware(use_device)
        self.fw_recommended=RecommendedFirmware(use_device,self.fw_installed,self.fw_available)
        self.target=self.fw_recommended.recommended.copy()

    def startup(self):
        if self.__check_arduino_cli_install():
            self.__create_arduino_config_file()
            return True
        return False

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

    def __check_arduino_cli_install(self):
        res=Popen('arduino-cli version', shell=True, bufsize=64, stdin=PIPE, stdout=PIPE,close_fds=True).stdout.read()[:11]
        if not(res==b'arduino-cli'):
            click.secho('WARNING:---------------------------------------------------------------------------------', fg="yellow", bold=True)
            click.secho('WARNING: Tool arduino_cli not installed. See stretch_install_dev.sh (Stretch Install repo)', fg="yellow", bold=True)
            click.secho('WARNING:---------------------------------------------------------------------------------', fg="yellow", bold=True)
            print('')
            return False
        return True

    def pretty_print_target(self):
        click.secho('################# UPDATING FIRMWARE TO... #################', fg="cyan", bold=True)
        for device_name in self.target.keys():
            if self.use_device[device_name]:
                if self.fw_installed.config_info[device_name] is None:
                    print('%s | No target available' % device_name.upper().ljust(25))
                else:
                    cfg = self.fw_installed.config_info[device_name]
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

        #Count how many updates doing
        for device_name in self.target.keys():
            if self.fw_installed.config_info[device_name] and self.target[device_name] is not None:
                if not (self.target[device_name]== self.fw_installed.config_info[device_name]['version']):
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
                if self.target[device_name] is not None:
                    if not (self.target[device_name]==self.fw_installed.config_info[device_name]['version']):
                        self.fw_updated[device_name]=self.flash_firmware_update(device_name,self.target[device_name].to_string())
            click.secho('---- Firmware Update Complete!', fg="green",bold=True)
            success=self.post_firmware_update()
            return success

    def do_update_to(self):
        # Return True if system was upgraded
        # Return False if system was not upgraded / error happened
        click.secho('######### Selecting target firmware versions ###########', fg="green", bold=True)
        for device_name in self.fw_recommended.recommended.keys():
            if self.use_device[device_name]:
                vs=self.fw_available.versions[device_name]
                if len(vs) and self.fw_recommended.recommended[device_name] is not None:
                    print('')
                    click.secho('---------- %s [%s]-----------'%(device_name.upper(),self.fw_installed.config_info[device_name]['board_info']['firmware_version']), fg="blue", bold=True)
                    default_id=0
                    for i in range(len(vs)):
                        if vs[i]==self.fw_recommended.recommended[device_name]:
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
        branches=self.fw_available.get_remote_branches()
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
                target_version=self.get_firmware_version_from_git(sketch_name, branch_name)
                git_protocol = 'p'+str(target_version.protocol)
                if not self.fw_installed.is_protocol_supported(device_name,git_protocol):
                    click.secho('---------------------------', fg="yellow")
                    click.secho('Target firmware branch of %s is incompatible with installed Stretch Body for device %s'%(branch_name,device_name),fg="yellow")
                    x = " , ".join(["{}"] * len(self.fw_installed.config_info[device_name]['supported_protocols'])).format(*self.config_info[device_name]['supported_protocols'])
                    click.secho('Installed Stretch Body supports protocols %s'%x,fg="yellow")
                    click.secho('Target branch supports protocol %s'%git_protocol,fg="yellow")
                    if git_protocol>self.fw_installed.max_protocol_supported(device_name):
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
                if self.fw_installed.config_info[device_name] is not None:
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
                    print('Successful write of FLASH.')
                    self.wait_on_device(device_name)
                    motor.board_reset()
                    motor.push_command()
                    motor.transport.ser.close()
                    time.sleep(2.0)
                    self.wait_on_device(device_name)
                    print('Successful return of device to bus.')



    def post_firmware_update(self,from_branch=False):
        #Return True if no errors
        for device_name in self.target.keys():
            if self.fw_updated[device_name]:
                self.flash_stepper_calibration(device_name)
        print('')
        click.secho('############## Confirming Firmware Updates ##############', fg="green", bold=True)
        self.fw_installed = InstalledFirmware(self.use_device) #Pull the currently installed system from fw
        success=True
        for device_name in self.target.keys():
            if self.use_device[device_name]:
                if self.fw_installed.config_info[device_name] is None: #Device may not have come back on bus
                    print('%s | No device available' % device_name.upper().ljust(25))
                    success=False
                else:
                    cfg = self.fw_installed.config_info[device_name]
                    v_curr = FirmwareVersion(cfg['board_info']['firmware_version'])  # Version that is now on the board
                    v_targ = self.target[device_name] if not from_branch else v_curr #Target version
                    if v_curr == v_targ:
                        click.secho('%s | %s ' % (device_name.upper().ljust(25), 'Installed firmware matches target'.ljust(40)),fg="green")
                    else:
                        click.secho('%s | %s ' % (device_name.upper().ljust(25), 'Firmware update failure!!'.ljust(40)),fg="red", bold=True)
                        success=False
        return success


    def get_firmware_version_from_git(self,sketch_name,tag):
        #click.secho('---------------Git Checkout-------------------------', fg="green")
        os.chdir(self.fw_available.repo_path)
        os.system('git checkout ' + tag +' >/dev/null 2>&1')
        print('Checked out out firmware %s from Git for %s' % (tag,sketch_name))
        file_path = self.fw_available.repo_path+'/arduino/'+sketch_name+'/Common.h'
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
        config_file = self.fw_available.repo_path + '/arduino-cli.yaml'
        sketch_name=None
        if device_name == 'hello-motor-left-wheel' or device_name == 'hello-motor-right-wheel' or device_name == 'hello-motor-arm' or device_name == 'hello-motor-lift':
            sketch_name = 'hello_stepper'
        if device_name == 'hello-wacc':
            sketch_name = 'hello_wacc'
        if device_name == 'hello-pimu':
            sketch_name = 'hello_pimu'
        port_name = self.get_port_name(device_name)
        if port_name is not None and sketch_name is not None:
            click.secho('---------------Git Checkout-------------------------', fg="green")
            os.chdir(self.fw_available.repo_path)
            os.system('git checkout '+tag+'>/dev/null 2>&1')
            print('Checkout out firmware %s from Git'%tag)
            click.secho('---------------Compile-------------------------', fg="green")
            compile_command = 'arduino-cli compile --config-file %s --fqbn hello-robot:samd:%s %s/arduino/%s'%(config_file,sketch_name,self.fw_available.repo_path,sketch_name)
            print(compile_command)
            c=Popen(compile_command, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip()
            print(c)
            click.secho('---------------Upload-------------------------', fg="green")
            upload_command = 'arduino-cli upload --config-file %s -p /dev/%s --fqbn hello-robot:samd:%s %s/arduino/%s' % (config_file, port_name, sketch_name, self.fw_available.repo_path,sketch_name)
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
