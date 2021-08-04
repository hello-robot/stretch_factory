#!/usr/bin/env python

import argparse
import serial.tools.list_ports
from subprocess import Popen, PIPE
# ###################################



class StretchSerialInfo:
    def __init__(self):
        self.comports= serial.tools.list_ports.comports()
        self.device_names = ['hello-motor-arm',
                             'hello-motor-lift',
                             'hello-motor-right-wheel',
                             'hello-motor-left-wheel',
                             'hello-dynamixel-wrist',
                             'hello-dynamixel-head']
        self.device_info={}
        for d in self.device_names:
            self.device_info[d]={'device':None,'info':None, 'core':None}

        #Build mapping between symlink and device name
        n_match=0
        lsdev=Popen("ls -ltr /dev/hello*", shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().split('\n')
        for name in self.device_info.keys():
            for line in lsdev:
                if line.find(name)>=0:
                    map=line[line.find(name):] #eg: hello-motor-arm -> ttyACM4
                    device=map[map.find('->')+3:] #eg ttyACM
                    self.device_info[name]['device']=device
                    n_match=n_match+1
        if not n_match==len(self.device_info.keys()):
            print('Failed to match all devices for StretchSerialInfo')
            print(self.device_info)
        for c in self.comports:
            for name in self.device_info.keys():
                if c.device[5:]==self.device_info[name]['device']:
                    self.device_info[name]['info']=c
        devs = []
        all = usb.core.find(find_all=True)
        for dev in all:
            if dev.idVendor == 0x2341 and dev.idProduct == 0x804d:
                devs.append(dev)
            if dev.idVendor == 0x0403 and dev.idProduct == 0x6001:
                devs.append(dev)
        n_match=0
        for name in self.device_info.keys():
            for d in devs:
                if d is not None and self.device_info[name]['info'] is not None:
                    if self.device_info[name]['info'].serial_number == d.serial_number:
                        n_match=n_match+1
                        self.device_info[name]['core']=d
        if not n_match==len(self.device_info.keys()):
            print('Failed to match all devices for StretchSerialInfo')
            print(self.device_info)



    def pretty_print(self):
        print('---- Stretch Serial Info ----')
        for name in self.device_info.keys():
            print('-----------------------------------------')
            print('%s : %s'%(name,self.device_info[name]['device']))
            if self.device_info[name]['info'] is not None:
                print('Serial: %s'%self.device_info[name]['info'].serial_number)
                print('Description: %s' % self.device_info[name]['info'].description)
                print('Location: %s' % self.device_info[name]['info'].location)

    def reset_all(self):
        print('Resetting all Stretch USB devices')
        print('---------------------------------')
        for name in self.device_info.keys():
            self.reset(name)

    def reset(self,name):
        if self.device_info[name]['core'] is not None:
            print('Resetting %s' % name)
            self.device_info[name]['core'].reset()
        else:
            print('Not able to reset device %s'%name)



if os.geteuid() == 0:
    s = StretchSerialInfo()
    parser = argparse.ArgumentParser(description='Software reset of Stretch USB devices')
    for d in s.device_names:
        parser.add_argument("--%s"%d, help="Reset %s"%d, action="store_true")
    args = parser.parse_args()
    any=False
    try:
        for d in s.device_names:
            if args.__dict__[d.replace('-','_')]: #argparse changes - to _
                s.reset(d)
                any=True
    except KeyError:
        print('Invalid argument')
        exit()
    if not any:
        s.reset_all()
else:
    success=False
    while not success: #Avoid incorrect entry of pass
        success=(subprocess.call(['sudo', 'python'] + sys.argv)==0)
