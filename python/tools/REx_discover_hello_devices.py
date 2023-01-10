#!/usr/bin/env python
import os
import unittest
from stretch_production_tools.bringup_test_utils import Bringup_Test
from stretch_production_tools.bringup_test_utils import BRI_TestRunner, BRI_TestSuite
from stretch_production_tools.production_test_utils import find_tty_devices
import stretch_body.stepper
import stretch_body.pimu
from stretch_body.dynamixel_XL430 import DynamixelXL430, DynamixelCommError
import stretch_body.wacc
import stretch_body.base
import time
import stretch_body.hello_utils as hu
from stretch_body.device import Device
import click
import pprint
from stretch_factory import hello_device_utils as hdu


def find_tty_devices():
    devices_dict = {}
    ttyUSB_dev_list = glob.glob('/dev/ttyUSB*')
    ttyACM_dev_list = glob.glob('/dev/ttyACM*')
    for d in ttyACM_dev_list:
        devices_dict[d] = {"serial": extract_udevadm_info(d, 'ID_SERIAL_SHORT'),
                           "vendor": extract_udevadm_info(d, 'ID_VENDOR'),
                           "model": extract_udevadm_info(d, 'ID_MODEL'),
                           "path": extract_udevadm_info(d, 'DEVPATH')}
    for d in ttyUSB_dev_list:
        devices_dict[d] = {"serial": extract_udevadm_info(d, 'ID_SERIAL_SHORT'),
                           "vendor": extract_udevadm_info(d, 'ID_VENDOR'),
                           "model": extract_udevadm_info(d, 'ID_MODEL'),
                           "path": extract_udevadm_info(d, 'DEVPATH')}
    return devices_dict


def extract_udevadm_info(usb_port, ID_NAME=None):
    """
    Extracts usb device attributes with the given attribute ID_NAME

    example ID_NAME:
    ID_SERIAL_SHORT
    ID_MODEL
    DEVPATH
    ID_VENDOR_FROM_DATABASE
    ID_VENDOR
    """
    value = None
    dname = bytes(usb_port[5:], 'utf-8')
    out = hdu.exec_process([b'udevadm', b'info', b'-n', dname], True)
    if ID_NAME is None:
        value = out.decode(encoding='UTF-8')
    else:
        for a in out.split(b'\n'):
            a = a.decode(encoding='UTF-8')
            if "{}=".format(ID_NAME) in a:
                value = a.split('=')[-1]
    return value


class DiscoverHelloDevices:
    def __int__(self):
        self.all_tty_devices = find_tty_devices()

