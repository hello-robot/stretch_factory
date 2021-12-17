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

def create_config_target_hi_res():
    f = open('/tmp/d435i_confg.cfg', "w+")
    f.write("DEPTH,1280,720,15,Z16,0\n")
    f.write("COLOR,1280,720,15,RGB8,0\n")
    f.write("ACCEL,1,1,63,MOTION_XYZ32F\n")
    f.write("GYRO,1,1,200,MOTION_XYZ32F\n")
    f.close()
    target = {'duration':31,
              'nframe':450,
              'margin':8,
              'streams':{
              'Color': {'target': 450, 'sampled': 0},
              'Depth': {'target': 450, 'sampled': 0},
              'Accel': {'target': 450, 'sampled': 0},
              'Gyro': {'target': 450, 'sampled': 0}}}
    return target


def create_config_target_low_res():
    f = open('/tmp/d435i_confg.cfg', "w+")
    f.write("DEPTH,424,240,30,Z16,0\n")
    f.write("COLOR,424,240,30,RGB8,0\n")
    f.write("ACCEL,1,1,63,MOTION_XYZ32F\n")
    f.write("GYRO,1,1,200,MOTION_XYZ32F\n")
    target = {'duration': 31,
              'nframe': 900,
              'margin': 16,
              'streams':{
              'Color': {'target': 900, 'sampled': 0},
              'Depth': {'target': 900, 'sampled': 0},
              'Accel': {'target': 900, 'sampled': 0},
              'Gyro': {'target': 900, 'sampled': 0}}}
    f.close()

def check_rate(data,target):
    for ll in data:
        for kk in target['streams'].keys():
            id=get_frame_id_from_log_line(kk,ll)
            if id is not None:
                target['streams'][kk]['sampled']=max(id,target['streams'][kk]['sampled'])
    for kk in target['streams'].keys():
        sampled_frames=target['streams'][kk]['sampled']
        min_frames=target['streams'][kk]['target']-target['margin']
        if sampled_frames>=min_frames:
            print(Fore.GREEN + '[Pass] Stream: %s with %d frames collected'%(kk,sampled_frames))
        else:
            print(Fore.RED + '[Fail] Stream: %s with %d frames of %d collected'%(kk,sampled_frames,min_frames))

def get_frame_id_from_log_line(stream_type,line):
    if line.find(stream_type)!=0:
        return None
    return int(line.split(',')[2])

def check_data_rate():
    # https://github.com/IntelRealSense/librealsense/tree/master/tools/data-collect
    print('---------- HIGH RES CHECK ----------')
    print('Checking high-res data rates. This will take 30s...')
    target=create_config_target_hi_res()
    cmd='rs-data-collect -c /tmp/d435i_confg.cfg -f /tmp/d435i_log.csv -t %d -m %d'%(target['duration'],target['nframe'])
    out = Popen(cmd, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE,close_fds=True).stdout.read()
    ff=open('/tmp/d435i_log.csv')
    data=ff.readlines()
    data=data[10:] #drop preamble
    check_rate(data,target)

    print('---------- LOW RES CHECK ----------')
    print('Checking low-res data rates. This will take 30s...')
    target=create_config_target_low_res()
    cmd='rs-data-collect -c /tmp/d435i_confg.cfg -f /tmp/d435i_log.csv -t %d -m %d'%(target['duration'],target['nframe'])
    out = Popen(cmd, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE,close_fds=True).stdout.read()
    ff=open('/tmp/d435i_log.csv')
    data=ff.readlines()
    data=data[10:] #drop preamble
    check_rate(data,target)
    
if args.usb:
    check_usb()

if args.rate:
    check_data_rate()
