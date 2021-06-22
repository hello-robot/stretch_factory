#!/usr/bin/env python
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


if os.geteuid() == 0:
    reset_arduino_usb()
    reset_FTDI_usb()
else:
    subprocess.call(['sudo', 'python'] + sys.argv)  # modified