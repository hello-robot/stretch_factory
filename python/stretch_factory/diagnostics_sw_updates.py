#!/usr/bin/env python
from __future__ import print_function
import stretch_body.robot as robot
import os, fnmatch
import subprocess
from colorama import Fore, Back, Style
import stretch_body.hello_utils as hu
from stretch_factory.diagnostics_utils import *

def find_latest_version_of_pip_package():

def diagnostics_sw_updates():
    # #####################################################
    result={'diagnostics_sw_updates':{
        'stretch_firmware':{},
        'stretch_body':{},
        'stretch_tool_share':{},
        'stretch_factory':{},
        'stretch_ros':{}}}

if __name__ == "__main__":
    result=diagnostics_sw_updates()
    print('########################################')
    hu.pretty_print_dict(title='Diagnostics SW Updates',d=result)