#!/usr/bin/env python
#import usb.core

import os
import sys
from subprocess import Popen, PIPE
import fcntl
import subprocess


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
# def reset_arduino_usb():
#     devs=[]
#     all = usb.core.find(find_all=True)
#     for dev in all:
#         if dev.idVendor==0x2341 and dev.idProduct==0x804d:
#             devs.append(dev)
#     print('Found %d Arduino devices'%len(devs))
#     for d in devs:
#         print('Resetting Arduino. Bus: %s | Device  %s ' % (d.bus, d.address))
#         try:
#             d.reset()
#         except usb.core.USBError:
#             print('Error in resetting device')
#
# def reset_FTDI_usb():
#     devs=[]
#     all = usb.core.find(find_all=True)
#     for dev in all:
#         if dev.idVendor==0x0403 and dev.idProduct==0x6001:
#             devs.append(dev)
#     print('Found %d FTDI devices'%len(devs))
#     for d in devs:
#         print('Resetting FTDI. Bus: %s | Device  %s ' % (d.bus, d.address))
#         try:
#             d.reset()
#         except usb.core.USBError:
#             print('Error in resetting device')

if os.geteuid() == 0:
    reset_arduino_usb()
    reset_FTDI_usb()
else:
    subprocess.call(['sudo', 'python'] + sys.argv)  # modified