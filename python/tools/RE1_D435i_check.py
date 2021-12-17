#!/usr/bin/env python
import argparse
import os
from subprocess import Popen, PIPE
from colorama import Fore, Back, Style

parser = argparse.ArgumentParser(description='Test the D435i basic function')
parser.add_argument("--usb", help="Test USB version", action="store_true")
parser.add_argument("--rate", help="Test data capture rate", action="store_true")
args = parser.parse_args()


def check_usb():
    out = Popen("rs-enumerate-devices| grep Usb | grep 3.2", shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read()
    if len(out):
        print(Fore.GREEN +'[Pass] Confirmed USB 3.2 connection to device')
    else:
        print(Fore.RED +'[Fail] Did not find USB 3.2 connection to device')

def create_config_file():
    f = open('/tmp/d435i_confg.cfg', "w+")
    f.write("DEPTH,1280,720,15,Z16,0\n")
    f.write("INFRARED,640,480,15,Y8,1\n")
    f.write("INFRARED,640,480,15,Y8,2\n")
    f.write("COLOR,1280,720,15,RGB8,0\n")
    f.write("ACCEL,1,1,63,MOTION_XYZ32F\n")
    f.write("GYRO,1,1,200,MOTION_XYZ32F\n")
    f.close()

def get_frame_id_from_log_line(stream_type,line):
    if line.find(stream_type)!=0:
        return None
    return int(line.split(',')[2])


def check_data_rate():
    print('Checking data rates. This will take 30s...')
    create_config_file()
    num_frames=450
    timeout=31
    cmd='rs-data-collect -c /tmp/d435i_confg.cfg -f /tmp/d435i_log.csv -t %d -m %d'%(timeout,num_frames)
    out = Popen(cmd, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE,close_fds=True).stdout.read()
    ff=open('/tmp/d435i_log.csv')
    data=ff.readlines()
    data=data[10:] #drop preamble
    result={'Color':{'target':num_frames-1,'sampled':0},'Depth':{'target':num_frames-1,'sampled':0},
            'Gyro':{'target':num_frames-1,'sampled':0},'Accel':{'target':num_frames-1,'sampled':0},
            'Infrared':{'target':num_frames-5,'sampled':0}}
    for ll in data:
        for kk in result.keys():
            id=get_frame_id_from_log_line(kk,ll)
            if id is not None:
                result[kk]['sampled']=max(id,result[kk]['sampled'])
    print(result)

if args.usb:
    check_usb()

if args.rate:
    check_data_rate()
