#!/usr/bin/env python
import os
import sys
from subprocess import Popen, PIPE
import fcntl
import subprocess
import usb.core


def reset_arduino_usb():
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

def reset_FTDI_usb():
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

if os.geteuid() == 0:
    reset_arduino_usb()
    reset_FTDI_usb()
else:
    success=False
    while not success: #Avoid incorrect entry of pass
        success=(subprocess.call(['sudo', 'python'] + sys.argv)==0)
