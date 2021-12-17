#!/usr/bin/env python
import argparse
import os
from subprocess import Popen, PIPE
from colorama import Fore, Back, Style

parser = argparse.ArgumentParser(description='Test the D435i basic function')
parser.add_argument("--usb", help="Test USB version", action="store_true")
parser.add_argument("--data_rate", help="Test data capture rate", action="store_true")
args = parser.parse_args()


def check_usb():
    out = Popen("rs-enumerate-devices| grep Usb | grep 3.2", shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read()
    if len(out):
        print(Fore.GREEN +'[Pass] Confirmed USB 3.2 connection to device')
    else:
        print(Fore.RED +'[Fail] Did not find USB 3.2 connection to device')

if args.usb:
    check_usb()


