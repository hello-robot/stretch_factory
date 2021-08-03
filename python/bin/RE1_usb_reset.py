#!/usr/bin/env python
import usb.core

import os
import sys
from subprocess import Popen, PIPE
import fcntl
import subprocess

import argparse

# ###################################


# devices={'hello-motor-arm','hello-motor-lift','hello-motor-right-wheel'}
# parser.add_argument("--device", type=str,help="Device to reset")
# args = parser.parse_args()
import serial.tools.list_ports
from subprocess import Popen, PIPE

class StretchSerialInfo:
    def __init__(self):
        self.comports= serial.tools.list_ports.comports()

        self.ports={'hello-motor-arm': {'device':None,'info':None},
                    'hello-motor-lift': {'device': None, 'info': None},
                    'hello-motor-right-wheel': {'device': None, 'info': None},
                    'hello-motor-left-wheel': {'device': None, 'info': None},
                    'hello-dynamixel-wrist': {'device': None, 'info': None},
                    'hello-dynamixel-head': {'device': None, 'info': None},
                    'hello-respeaker': {'device': None, 'info': None},
                    'hello-lrf':  {'device': None, 'info': None}}

        #Build mapping between symlink and device name
        lsdev=Popen("ls -ltr /dev/hello*", shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().split('\n')
        for name in self.ports.keys():
            for line in lsdev:
                if line.find(name)>=0:
                    map=line[line.find(name):] #eg: hello-motor-arm -> ttyACM4
                    device=map[map.find('->')+3:] #eg ttyACM
                    self.ports[name]['device']=device

        for c in self.comports:
            for name in self.ports.keys():
                if c.device[5:]==self.ports[name]['device']:
                    self.ports[name]['info']=c
    def pretty_print(self):
        print('---- Stretch Serial Info ----')
        for name in self.ports.keys():
            print('-----------------------------------------')
            print('%s : %s'%(name,self.ports[name]['device']))
            if self.ports[name]['info'] is not None:
                print('Serial: %s'%self.ports[name]['info'].serial_number)
                print('Description: %s' % self.ports[name]['info'].description)
                print('Location: %s' % self.ports[name]['info'].location)

    def reset(self,name):
        print('Resetting %s. Bus: %s | Device  %s ' % (name,bus, device))
        f = open("/dev/bus/usb/%s/%s" % (bus, device), 'w', os.O_WRONLY)
        fcntl.ioctl(f, USBDEVFS_RESET, 0)
        # for port in self.ports_list:
        #     if port.vid==0x2341 and port.pid==0x804d: #Arduino
        #         pass
        #     if port.vid == 0x0403 and port.pid == 0x6001:  # FTDI
        #         pass

s=StretchSerialInfo()
s.pretty_print()

# devs = []
# all = usb.core.find(find_all=True)
# for dev in all:
#     if dev.idVendor == 0x2341 and dev.idProduct == 0x804d:
#         devs.append(dev)
# print('Found %d Arduino devices' % len(devs))
# for d in devs:
#     print('Resetting Arduino. Bus: %s | Device  %s ' % (d.bus, d.address))
    #f = open("/dev/bus/usb/%s/%s" % (d.bus, d.address), 'w', os.O_WRONLY)
    #fcntl.ioctl(f, USBDEVFS_RESET, 0)
    # try:
    #     d.reset()
    # except usb.core.USBError:
    #     print('Error in resetting device')


# def get_bus_device_no(port):
#     cmd = "echo `udevadm info - -name = / dev / hello - motor - arm - -attribute - walk | sed - n 's/\s*ATTRS{\(\(devnum\)\|\(busnum\)\)}==\"\([^\"]\+\)\"/\1\ \4/p' | head - n2 | awk '{$1 = sprintf("%s:%03d", $1, $2); print $1;}'"`


def reset_arduino_usb():
    USBDEVFS_RESET = 21780
    lsusb_out = Popen("lsusb | grep -i %s" % 'Arduino', shell=True, bufsize=64, stdin=PIPE, stdout=PIPE,
                      close_fds=True).stdout.read().strip().split()
    while len(lsusb_out):
        bus = lsusb_out[1]
        device = lsusb_out[3][:-1]
        try:
            print('Resetting Arduino. Bus: %s | Device  %s '%(bus, device))
            f = open("/dev/bus/usb/%s/%s" % (bus, device), 'w', os.O_WRONLY)
            fcntl.ioctl(f, USBDEVFS_RESET, 0)
        except Exception as msg:
            print("failed to reset device: %s" % msg)
        lsusb_out = lsusb_out[8:]

def reset_FTDI_usb():
    USBDEVFS_RESET = 21780
    lsusb_out = Popen("lsusb | grep -i %s"%'Future', shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read().strip().split()
    while len(lsusb_out):
        bus = lsusb_out[1]
        device = lsusb_out[3][:-1]
        try:
            print('Resetting FTDI. Bus: %s | Device  %s '%(bus, device))
            f = open("/dev/bus/usb/%s/%s" % (bus, device), 'w', os.O_WRONLY)
            fcntl.ioctl(f, USBDEVFS_RESET, 0)

        except Exception as msg:
            print("failed to reset device: %s"%msg)
        lsusb_out=lsusb_out[15:]

# if os.geteuid() == 0:
#     reset_arduino_usb()
#     reset_FTDI_usb()
# else:
#     subprocess.call(['sudo', 'python'] + sys.argv)  # modified
def reset_arduino_usb2():
    devs=[]
    all = usb.core.find(find_all=True)
    for dev in all:
        if dev.idVendor==0x2341 and dev.idProduct==0x804d:
            devs.append(dev)
    print('Found %d Arduino devices'%len(devs))
    for d in devs:
        print('Resetting Arduino. Bus: %s | Device  %s ' % (d.bus, d.address))
        try:
            d.reset()
        except usb.core.USBError:
            print('Error in resetting device')

def reset_FTDI_usb2():
    devs=[]
    all = usb.core.find(find_all=True)
    for dev in all:
        if dev.idVendor==0x0403 and dev.idProduct==0x6001:
            devs.append(dev)
    print('Found %d FTDI devices'%len(devs))
    for d in devs:
        print('Resetting FTDI. Bus: %s | Device  %s ' % (d.bus, d.address))
        try:
            d.reset()
        except usb.core.USBError:
            print('Error in resetting device')

# if os.geteuid() == 0:
#     reset_arduino_usb()
#     reset_FTDI_usb()
# else:
#     subprocess.call(['sudo', 'python'] + sys.argv)  # modified