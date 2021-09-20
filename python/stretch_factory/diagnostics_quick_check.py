#!/usr/bin/env python
from __future__ import print_function
import stretch_body.robot as robot
import os, fnmatch
import subprocess
from colorama import Fore, Back, Style
import stretch_body.hello_utils as hu
from stretch_factory.diagnostics_utils import *

def diagnostics_quick_check():
    # #####################################################
    result={'diagnostics_quick_check':{
        'hello-wacc':{}, 
        'hello-motor-left-wheel':{},
        'hello-pimu':{}, 
        'hello-lrf':{},
        'hello-dynamixel-head':{},
        'hello-dynamixel-wrist':{},
        'hello-motor-arm':{},
        'hello-motor-right-wheel':{},
        'hello-motor-lift':{},
        'hello-respeaker':{},
        'd435i':{}}}

    r=robot.Robot()
    r.startup()

    # #####################################################
    print(Style.RESET_ALL)
    print('---- Checking Devices ----')
    robot_devices={'hello-wacc':0, 'hello-motor-left-wheel':0,'hello-pimu':0, 'hello-lrf':0,'hello-dynamixel-head':0,'hello-dynamixel-wrist':0,'hello-motor-arm':0,'hello-motor-right-wheel':0,
                   'hello-motor-lift':0,'hello-respeaker':0}

    listOfFiles = os.listdir('/dev')
    pattern = "hello*"
    for entry in listOfFiles:
        if fnmatch.fnmatch(entry, pattern):
                robot_devices[entry]=1
    for k in robot_devices.keys():

        if robot_devices[k]:
            result['diagnostics_quick_check'][k]['device_on_bus']=True
            print(Fore.GREEN +'[Pass] : '+k)
        else:
            result['diagnostics_quick_check'][k]['device_on_bus']= False
            print(Fore.RED +'[Fail] : '+ k)
    # #####################################################

    print(Style.RESET_ALL)
    result['diagnostics_quick_check']['hello-pimu']['in_range'] = {}
    if robot_devices['hello-pimu']:
        print('---- Checking Pimu ----')
        p=r.pimu
        result['diagnostics_quick_check']['hello-pimu']['in_range']['voltage']=val_in_range('Voltage',p.status['voltage'], vmin=p.config['low_voltage_alert'], vmax=14.5)
        result['diagnostics_quick_check']['hello-pimu']['in_range']['current']=val_in_range('Current',p.status['current'], vmin=0.5, vmax=p.config['high_current_alert'])
        result['diagnostics_quick_check']['hello-pimu']['in_range']['temp']=val_in_range('Temperature',p.status['temp'], vmin=10, vmax=40)
        result['diagnostics_quick_check']['hello-pimu']['in_range']['cliff_range_0']=val_in_range('Cliff-0',p.status['cliff_range'][0], vmin=p.config['cliff_thresh'], vmax=20)
        result['diagnostics_quick_check']['hello-pimu']['in_range']['cliff_range_1']=val_in_range('Cliff-1',p.status['cliff_range'][1], vmin=p.config['cliff_thresh'], vmax=20)
        result['diagnostics_quick_check']['hello-pimu']['in_range']['cliff_range_2']=val_in_range('Cliff-2',p.status['cliff_range'][2], vmin=p.config['cliff_thresh'], vmax=20)
        result['diagnostics_quick_check']['hello-pimu']['in_range']['cliff_range_3']=val_in_range('Cliff-3',p.status['cliff_range'][3], vmin=p.config['cliff_thresh'], vmax=20)
        result['diagnostics_quick_check']['hello-pimu']['in_range']['imu_az']=val_in_range('IMU AZ',p.status['imu']['az'], vmin=-10.1, vmax=-9.5)
        result['diagnostics_quick_check']['hello-pimu']['in_range']['imu_pitch']=val_in_range('IMU Pitch', hu.rad_to_deg(p.status['imu']['pitch']), vmin=-12, vmax=12)
        result['diagnostics_quick_check']['hello-pimu']['in_range']['imu_roll']=val_in_range('IMU Roll', hu.rad_to_deg(p.status['imu']['roll']), vmin=-12, vmax=12)
        print(Style.RESET_ALL)

    # #####################################################
    print(Style.RESET_ALL)
    if robot_devices['hello-dynamixel-wrist']:
        print('---- Checking EndOfArm ----')
        w = r.end_of_arm
        try:
            for mk in w.motors.keys():
                result['diagnostics_quick_check']['hello-dynamixel-wrist'][mk]={}
                if w.motors[mk].do_ping():
                    result['diagnostics_quick_check']['hello-dynamixel-wrist'][mk]['ping']=True
                    print(Fore.GREEN +'[Pass] Ping of: '+mk)
                    if w.motors[mk].params['req_calibration']:
                        if w.motors[mk].motor.is_calibrated():
                            print(Fore.GREEN + '[Pass] Calibrated: ' + mk)
                            result['diagnostics_quick_check']['hello-dynamixel-wrist'][mk]['calibrated'] = True
                        else:
                            print(Fore.RED + '[Fail] Not Calibrated: ' + mk)
                            result['diagnostics_quick_check']['hello-dynamixel-wrist'][mk]['calibrated'] = False
                else:
                    result['diagnostics_quick_check']['hello-dynamixel-wrist'][mk]['ping'] = False
                    print(Fore.RED + '[Fail] Ping of: ' + mk)
                print(Style.RESET_ALL)
        except IOError:
            print(Fore.RED + '[Fail] Startup of EndOfArm')
    # #####################################################
    print(Style.RESET_ALL)
    if robot_devices['hello-dynamixel-head']:
        print('---- Checking Head ----')
        h = r.head
        for mk in h.motors.keys():
            result['diagnostics_quick_check']['hello-dynamixel-head'][mk] = {}
            if h.motors[mk].do_ping():
                print(Fore.GREEN +'[Pass] Ping of: '+mk)
                result['diagnostics_quick_check']['hello-dynamixel-head'][mk]['ping'] = True
            else:
                print(Fore.RED + '[Fail] Ping of: ' + mk)
                result['diagnostics_quick_check']['hello-dynamixel-head'][mk]['ping'] = False
            print(Style.RESET_ALL)

    # #####################################################
    print(Style.RESET_ALL)
    result['diagnostics_quick_check']['hello-wacc']['in_range'] = {}
    if robot_devices['hello-wacc']:
        print('---- Checking Wacc ----')
        w=r.wacc
        result['diagnostics_quick_check']['hello-wacc']['in_range']['ax']=val_in_range('AX',w.status['ax'], vmin=8.0, vmax=11.0)
        print(Style.RESET_ALL)

    # #####################################################
    print(Style.RESET_ALL)
    if robot_devices['hello-motor-left-wheel']:
        print('---- Checking hello-motor-left-wheel ----')
        m = r.base.left_wheel
        result['diagnostics_quick_check']['hello-motor-left-wheel']['pos_not_zero']=val_is_not('Position',m.status['pos'], vnot=0)
        print(Style.RESET_ALL)
        m.stop()
    # #####################################################
    print(Style.RESET_ALL)
    if robot_devices['hello-motor-right-wheel']:
        print('---- Checking hello-motor-right-wheel ----')
        m = r.base.right_wheel
        result['diagnostics_quick_check']['hello-motor-right-wheel']['pos_not_zero']=val_is_not('Position',m.status['pos'], vnot=0)
        print(Style.RESET_ALL)

    # #####################################################
    print(Style.RESET_ALL)
    if robot_devices['hello-motor-arm']:
        print('---- Checking hello-motor-arm ----')
        m = r.arm.motor
        result['diagnostics_quick_check']['hello-motor-right-wheel']['pos_not_zero']=val_is_not('Position',m.status['pos'], vnot=0)
        result['diagnostics_quick_check']['hello-motor-right-wheel']['calibrated']=val_is_not('Position Calibrated', m.status['pos_calibrated'], vnot=False)
        print(Style.RESET_ALL)

    # #####################################################
    print(Style.RESET_ALL)
    if robot_devices['hello-motor-lift']:
        print('---- Checking hello-motor-lift ----')
        m = r.lift.motor
        result['diagnostics_quick_check']['hello-motor-lift']['pos_not_zero']=val_is_not('Position',m.status['pos'], vnot=0)
        result['diagnostics_quick_check']['hello-motor-lift']['pos_not_zero']=val_is_not('Position Calibrated', m.status['pos_calibrated'], vnot=False)
        print(Style.RESET_ALL)

    # #####################################################
    print(Style.RESET_ALL)
    print ('---- Checking for Intel D435i ----')
    cmd = "lsusb -d 8086:0b3a"
    returned_value = subprocess.call(cmd,shell=True)  # returns the exit code in unix
    if returned_value==0:
        result['diagnostics_quick_check']['d435i']['device_on_bus']=print(Fore.GREEN + '[Pass] : Device found ')
    else:
        result['diagnostics_quick_check']['d435i']['device_on_bus']=print(Fore.RED + '[Fail] : No device found')
    r.stop()
    print(Style.RESET_ALL)
    return result

if __name__ == "__main__":
    result=diagnostics_quick_check()
    print('########################################')
    hu.pretty_print_dict(title='Diagnostics Quick Check',d=result)