#!/usr/bin/env python
import argparse
import click
from colorama import Style
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import stretch_body.robot
import stretch_body.hello_utils as hu
from os import makedirs
import yaml
from yaml import CDumper as Dumper

hu.print_stretch_re_use()

parser = argparse.ArgumentParser(description='Tool to load and view the firmware trace data.', )
args = parser.parse_args()
robot=stretch_body.robot.Robot()
if not robot.startup():
    exit(1)


class TraceMgmt:
    """
    Manage trace data
    """
    def __init__(self):
        self.device_names = ['pimu', 'wacc', 'right_wheel', 'left_wheel', 'lift', 'arm']
        self.trace_directory = hu.get_stretch_directory() + 'log/trace_firmware'
        try:
            makedirs(self.trace_directory)
        except OSError:
            pass  # Exists

    def get_int(self,range,msg='value'):
        while True:
            result = input("Enter %s (range %d to %d):  "%(msg,range[0],range[1]))
            if result.isdigit() and range[0] <= int(result) <= range[1]:
                return int(result)
            print("Error Invalid Input")

    def run_menu(self):
        trace_data=[]
        device_name=''

        while True:
            if len(trace_data):
                click.secho('Current trace: Device %s | Duration (s): %f | Start timestamp %f: ' % (
                device_name, (trace_data[-1]['status']['timestamp']-trace_data[0]['status']['timestamp'])/1000000.0,trace_data[0]['status']['timestamp']), fg="green", bold=True)
            else:
                click.secho('No trace loaded', fg="yellow", bold=True)
            print('')
            print(Style.BRIGHT + '############### MENU ################' + Style.RESET_ALL)
            print('Enter command. (q to quit)')
            print('r: record trace on device')
            print('d: load trace from device')
            print('l: load trace from file')
            print('s: save trace to file')
            print('p: plot trace')
            print('x: print trace to console')
            print('-------------------------------------')
            #try:
            r = input()
            if r == 'q' or r == 'Q':
                return
            elif r=='r':
                trace_data,device_name=self.record_trace()
            elif r=='d':
                trace_data,device_name=self.load_trace_from_device()
            elif r=='l':
                trace_data,device_name=self.load_trace_from_file()
            elif r == 's':
                self.save_trace(trace_data,device_name)
            elif r == 'p':
                self.do_plot(trace_data,device_name)
            elif r== 'x':
                print(trace_data)
            else:
                print('Invalid entry')
            # except(TypeError, ValueError):
            #     print('Invalid entry')

    def record_trace(self):
        device_id=self.get_device_id()
        print('')
        dd=None
        device_name=self.device_names[device_id]
        if  device_name== 'pimu':
            dd = robot.pimu
        if device_name == 'wacc':
            dd = robot.wacc
        if device_name == 'right_wheel':
            dd =robot.base.right_wheel
        if device_name == 'left_wheel':
            dd =robot.base.left_wheel
        if device_name == 'lift':
            dd =robot.lift.motor
        if device_name == 'arm':
            dd =robot.arm.motor
        if dd is not None:
            input("Hit enter to begin recording")
            dd.enable_firmware_trace()
            robot.push_command()
            print('\nRecording...\n')
            input("Hit enter to end recording")
            dd.disable_firmware_trace()
            robot.push_command()

        print('Reading trace back from recording. This may take a minute...')
        trace_data = dd.read_firmware_trace()
        if len(trace_data)==0:
            print('No trace data found for %s'%device_name)
        return trace_data, device_name

    def load_trace_from_file(self):
            # Retrieve sorted list of all trace files
            all_files = glob.glob(self.trace_directory + '/*.yaml')
            all_files.sort()
            if len(all_files):
                print('--- Firmware Trace Files ---')
                for i in range(len(all_files)):
                    print('%d: %s'%(i,all_files[i]))
                fn=all_files[self.get_int([0,len(all_files)-1],'FILE_ID')]
                ll=fn[fn.find('trace_fw_')+9:]
                device_name=ll[:ll.find('_')]
                with open(fn, 'r') as s:
                    return(yaml.load(s, Loader=yaml.FullLoader),device_name)
            else:
                print('No trace files available')
            return [],''

    def get_device_id(self):
        print(Style.BRIGHT + '############### Devices ################' + Style.RESET_ALL)
        for i in range(len(self.device_names)):
            print('%d: %s' % (i, self.device_names[i]))
        print('')
        device_id = self.get_int([0, 5], 'device ID')

        return device_id
    def load_trace_from_device(self):
        device_id=self.get_device_id()
        print('')
        print('Reading trace from device. This may take a minute...')
        print('')
        trace_data = []
        device_name = self.device_names[device_id]
        if self.device_names[device_id] == 'pimu':
            trace_data = robot.pimu.read_firmware_trace()
        if self.device_names[device_id] == 'wacc':
            trace_data = robot.wacc.read_firmware_trace()
        if self.device_names[device_id] == 'right_wheel':
            trace_data = robot.base.right_wheel.read_firmware_trace()
        if self.device_names[device_id] == 'left_wheel':
            trace_data = robot.base.left_wheel.read_firmware_trace()
        if self.device_names[device_id] == 'lift':
            trace_data = robot.lift.motor.read_firmware_trace()
        if self.device_names[device_id] == 'arm':
            trace_data = robot.arm.motor.read_firmware_trace()
        if len(trace_data)==0:
            print('No trace data found for %s'%device_name)
        return trace_data, device_name

    def save_trace(self,trace_data,device_name):
        if len(trace_data)==0:
            print('No trace data to save')
            return

        time_string = hu.create_time_string()
        fn = self.trace_directory + '/trace_fw_' + device_name + '_' +time_string+'.yaml'
        print('Creating trace: %s'%fn)
        with open(fn, 'w+') as fh:
            fh.write('###%s###\n'%device_name)
            yaml.dump(trace_data, fh, encoding='utf-8', default_flow_style=False, Dumper=Dumper) #Use C YAML dumper for 5x speed increase over Python



    def do_plot(self,trace_data,device_name):
        print(Style.BRIGHT + '############### Plotting ################' + Style.RESET_ALL)
        print('----- Trace Fields -----')
        s0=trace_data[0]['status']
        kk=list(s0.keys())
        kk.sort()
        field_keys=[]
        for k in kk:
            if type(s0[k])==int or type(s0[k])==float or type(s0[k])==bool:
                field_keys.append(k)
                print('%d: %s'%(len(field_keys)-1,str(k)))
        print('')
        field_name=field_keys[self.get_int([0,len(field_keys)-1],'FIELD ID')]
        data=[]
        for t in trace_data:
            data.append(t['status'][field_name])
        print('---------- PLOT DATA ----------')
        print(data)
        print('')

        plt.ion()  # enable interactivity
        fig, axes = plt.subplots(1, 1, figsize=(15.0, 8.0), sharex=True)
        fig.canvas.set_window_title('TRACE %s | %s'%(device_name.upper(),field_name.upper()))
        axes.set_yscale('linear')
        axes.set_xlabel('Sample')
        axes.set_ylabel(field_name.upper())
        axes.grid(True)
        axes.plot(data, 'b')
        fig.canvas.draw_idle()


mgmt=TraceMgmt()
mgmt.run_menu()