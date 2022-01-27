#!/usr/bin/env python
import argparse
from concurrent.futures import thread
import os
import sys
from subprocess import Popen, PIPE
from colorama import Fore, Back, Style
import stretch_factory.hello_device_utils as hdu
from threading import Thread
import time
import numpy as np
import stretch_body.robot

parser = argparse.ArgumentParser(description='Test the D435i basic function')
parser.add_argument("--usb", help="Test USB version", action="store_true")
parser.add_argument("--rate", help="Test data capture rate", action="store_true")
parser.add_argument("--scan_head", help="Test data capture rate with Head Pan and Tilt to extremity", action="store_true")
parser.add_argument('-f', metavar='dmesg_path', type=str, help='The path to save D435i Check Log (default:/tmp/d435i_check_log.txt)')
args = parser.parse_args()
thread_stop = False
check_log = []
dmesg_log = []
log_file_path = "/tmp/d435i_check_log.txt"

# Include all the known kernel non problematic messages here
# index     1:no.occured 2:no.Acceptable_Occurances 3:Message
known_msgs=[[0,15,'uvcvideo: Failed to query (GET_CUR) UVC control'],
            [0,4,'Non-zero status (-71) in video completion handler'],
            [0,4,'No report with id 0xffffffff found'],
            [0,10,'uvcvideo: Found UVC 1.50 device Intel(R) RealSense(TM) Depth Camera 435'],
            [0,5,'uvcvideo: Unable to create debugfs 2-2 directory.'],
            [0,4,'hid-sensor-hub'],
            [0,6,'input: Intel(R) RealSense(TM) Depth Ca'],
            [0,1,'uvcvideo: Failed to resubmit video URB (-1).']]

pan_tilt_pos = (None,None)
usbtop_cmd = None

# Avg Throughput threshold values based on tests 
out_speed_thresh_high_res = 36000 # Kib/s
out_speed_thresh_low_res = 10000 # Kib/s

def get_usb_busID():
    """
    Search for Realsense D435i in the USB bus
    Gets the USB Bus number and device ID for monitoring
    Execute it at Start
    """
    global usbtop_cmd, check_log
    print('Starting D435i Check')
    print('====================')
    print('Searching for Realsense D435i in USB Bus...')
    out = Popen("usb-devices | grep -B 5 -i 'RealSense' | grep -i 'Bus'", shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read()
    if(len(out)):
        out_list = out.split(' ')
        bus_no = None
        dev_id = None
        usb_found = False
        for i in range(len(out_list)):
            if out_list[i].find('Bus')!=-1:
                bus_no = out_list[i].split('=')[1]
                bus_no = int(bus_no)
            if out_list[i]=='Dev#=':
                dev_id = int(out_list[i+2])

        print(Fore.GREEN + '[Pass] Realsense D435i found at USB Bus_No : %d | Device ID : %d'%(bus_no,dev_id)+Style.RESET_ALL)
        check_log.append('[Pass] Realsense D435i found at USB Bus_No : %d | Device ID : %d'%(bus_no,dev_id))

        usbtop_cmd = "sudo usbtop --bus usbmon%d | grep 'Device ID %d' > /tmp/usbrate.txt"%(bus_no,dev_id)
    else:
        print(Fore.RED + '[Fail] Realsense D435i not found at USB Bus'+Style.RESET_ALL)
        check_log.append('[Fail] Realsense D435i not found at USB Bus')
        sys.exit()         

def check_usb():
    global check_log
    out = Popen("rs-enumerate-devices| grep Usb | grep 3.2", shell=True, bufsize=64, stdin=PIPE, stdout=PIPE, close_fds=True).stdout.read()
    if len(out):
        print(Fore.GREEN +'[Pass] Confirmed USB 3.2 connection to device'+Style.RESET_ALL)
        check_log.append('[Pass] Confirmed USB 3.2 connection to device')
    else:
        print(Fore.RED +'[Fail] Did not find USB 3.2 connection to device'+Style.RESET_ALL)
        check_log.append('[Fail] Did not find USB 3.2 connection to device')
    
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
    return target

def check_frames_collected(data,target):
    global check_log
    check_log.append('\nRate Check Results......\n')
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
            check_log.append('[Pass] Stream: %s with %d frames collected'%(kk,sampled_frames))
        else:
            print(Fore.RED + '[Fail] Stream: %s with %d frames of %d collected'%(kk,sampled_frames,min_frames))
            check_log.append('[Fail] Stream: %s with %d frames of %d collected'%(kk,sampled_frames,min_frames))
    print(Style.RESET_ALL)

def get_frame_id_from_log_line(stream_type,line):
    if line.find(stream_type)!=0:
        return None
    return int(line.split(',')[2])

def check_dmesg(msgs):
    global known_msgs
    print('\nDMESG Issues.....')
    unknown_msgs=[]
    no_error=True
    for m in msgs:
        if len(m):
            found=False
            for i in range(len(known_msgs)):
                if m.find(known_msgs[i][2])!=-1:
                    found=True
                    known_msgs[i][0]=known_msgs[i][0]+1
            if not found:
                unknown_msgs.append(m)
    for i in range(len(known_msgs)):
        if known_msgs[i][0]>=known_msgs[i][1]:
            print(Fore.YELLOW+'[Warning] Excessive dmesg warnings (%d) of: %s'%(known_msgs[i][0],known_msgs[i][2]))
            no_error=False
    if len(unknown_msgs):
        print('[Warning] Unexpected dmesg warnings (%d)'%len(unknown_msgs))
        no_error=False
        for i in unknown_msgs:
            print(i)
    if no_error:
        print(Fore.GREEN+'[Pass] No unexpected dmesg warnings')
    print(Style.RESET_ALL)

def check_dmesg_thread():
    global thread_stop, check_log, pan_tilt_pos, dmesg_log
    print('\nMonitoring the DMESG Buffer for issues while collecting camera stream.\n\n')
    while thread_stop==False:
        out = hdu.exec_process(['sudo', 'dmesg','-c'], True).split('\n')
        if len(out)>0:
            for mesg in out:
                if len(mesg)>0:
                    if pan_tilt_pos[0]:
                        check_log.append(mesg+'   (Pan, Tilt)='+str(pan_tilt_pos))
                        dmesg_log.append(mesg)
                    else:
                        check_log.append(mesg)
                        dmesg_log.append(mesg)

def check_throughput(usbrate_file,out_thresh):
    global check_log
    ff = open(usbrate_file)
    data = ff.readlines()
    ff.close()
    hdu.exec_process(['sudo', 'rm', '/tmp/usbrate.txt'], True)
    in_speed_list = []
    out_speed_list = []
    for ll in data:
        line = ll.split('\t')
        if(len(line)==5):

            try:
                in_speed = float(line[3].split(' ')[0]) #Kib/s
                in_speed_list.append(in_speed)
            except:
                None
            try:
                out_speed = float(line[4].split(' ')[0]) #Kib/s
                out_speed_list.append(out_speed)
            except:
                None
 
    avg_in_speed = sum(in_speed_list)/len(in_speed_list)
    max_in_speed = max(in_speed_list)
    avg_out_speed = sum(out_speed_list)/len(out_speed_list)
    max_out_speed = max(out_speed_list)

    check_log.append('Max From Device Speed : %f Kib/s'%(max_out_speed))
    check_log.append('Avg From Device Speed : %f Kib/s'%(avg_out_speed))
    check_log.append('Avg To Device Speed : %f Kib/s'%(avg_in_speed))
    check_log.append('Max To Device Speed : %f Kib/s'%(max_in_speed))

    if out_thresh < avg_out_speed:
        print(Fore.GREEN + '[Pass] Avg From Device Speed : %f Kib/s'%(avg_out_speed))
        print(Fore.GREEN + '[Pass] Max From Device Speed : %f Kib/s'%(max_out_speed))
    else:
        print(Fore.RED + '[Fail] Avg From Device Speed : %f Kib/s lower than %d Kib/s'%(avg_out_speed,out_thresh))
        print(Fore.RED + '[Fail] Max From Device Speed : %f Kib/s'%(max_out_speed))

    print(Style.RESET_ALL+'Avg To Device Speed : %f Kib/s'%(avg_in_speed))
    print('Max To Device Speed : %f Kib/s'%(max_in_speed))   
    print('\n')

def check_data_rate(target,robot=None):
    global check_log
    # https://github.com/IntelRealSense/librealsense/tree/master/tools/data-collect

    usbtop_proc = Popen(usbtop_cmd, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE,close_fds=True)

    if robot:
        scan_head_thread = Thread(target=scan_head_sequence,args=[robot,])
        scan_head_thread.start()

    cmd='rs-data-collect -c /tmp/d435i_confg.cfg -f /tmp/d435i_log.csv -t %d -m %d'%(target['duration'],target['nframe'])
    out = Popen(cmd, shell=True, bufsize=64, stdin=PIPE, stdout=PIPE,close_fds=True).stdout.read()
    usbtop_proc.terminate()

    ff=open('/tmp/d435i_log.csv') 
    data=ff.readlines()
    data=data[10:] #drop preamble
    check_frames_collected(data,target)

    if robot:
        scan_head_thread.join()

def get_head_pos(robot,Print=False):
    tilt_pos = robot.status['head']['head_tilt']['pos']
    pan_pos = robot.status['head']['head_pan']['pos']
    if Print:
        print('Head Tilt: %f | Pan: %f' % (tilt_pos,pan_pos))
    return (pan_pos,tilt_pos)

def save_collected_log(check_log):
    print('---------- COLLECTED LOG ----------')
    check_log_str = ''
    for ll in check_log:
        check_log_str = check_log_str + ll + '\n'
    
    check_log_file = open(log_file_path,"w")
    check_log_file.write(check_log_str)
    print('Collected D435i Check log saved at "'+log_file_path+'"')

def scan_head_sequence(robot):
    """
    Head Pan Tilt Sequence
    """
    global pan_tilt_pos
    robot.head.home()
    time.sleep(1)

    n = 60
    delay = 0.1
    tilt_moves = np.linspace(-1.57,0,n)
    pan_moves = np.linspace(1.57,-3.14,n)

    for i in range(n):
        robot.head.move_to('head_tilt',tilt_moves[i])
        robot.head.move_to('head_pan',pan_moves[i])
        time.sleep(delay)
        pan_tilt_pos = get_head_pos(robot)
    time.sleep(0.8)

    for i in range(n):
        robot.head.move_to('head_tilt',np.flip(tilt_moves)[i])
        robot.head.move_to('head_pan',np.flip(pan_moves)[i])
        time.sleep(delay)
        pan_tilt_pos = get_head_pos(robot)
    time.sleep(0.8)
        
    for i in range(n):
        robot.head.move_to('head_tilt',np.flip(tilt_moves)[i])
        robot.head.move_to('head_pan',pan_moves[i])
        time.sleep(delay)
        pan_tilt_pos = get_head_pos(robot)
    time.sleep(0.8)

    for i in range(n):
        robot.head.move_to('head_tilt',tilt_moves[i])
        robot.head.move_to('head_pan',np.flip(pan_moves)[i])
        time.sleep(delay)
        pan_tilt_pos = get_head_pos(robot)
    time.sleep(0.8)
    robot.head.home()

def scan_head_check_rate():
    """
    Check D435i rates with head moving to extremities
    """
    global thread_stop, dmesg_log
    check_install_usbtop()
    get_usb_busID()
    check_usb()
    robot=stretch_body.robot.Robot()
    robot.startup()

    hdu.exec_process(['sudo', 'dmesg', '-c'], True)
    hdu.exec_process(['sudo', 'modprobe', 'usbmon'], True)
    thread_stop = False
    monitor_dmesg = Thread(target=check_dmesg_thread)
    monitor_dmesg.start()

    conf_type = '---------- HIGH RES CHECK ----------'
    check_log.append('\n'+conf_type + '\n')


    print(conf_type)
    print('Checking high-res data rates. This will take 30s...')
    target=create_config_target_hi_res()
    check_data_rate(target,robot)
    check_throughput('/tmp/usbrate.txt',out_speed_thresh_high_res)
    time.sleep(1.5)

    conf_type = '---------- LOW RES CHECK ----------'
    check_log.append('\n'+conf_type + '\n')
    print(conf_type)
    print('Checking low-res data rates. This will take 30s...')
    target=create_config_target_low_res()
    check_data_rate(target,robot)
    check_throughput('/tmp/usbrate.txt',out_speed_thresh_low_res)
    time.sleep(1.5)

    thread_stop = True
    monitor_dmesg.join()
    
    check_dmesg(dmesg_log)
    save_collected_log(check_log)

    
    robot.stop()

def check_rate_exec():
    """
    Check D435i rates without head moving
    """
    global thread_stop, dmesg_log
    check_install_usbtop()
    get_usb_busID()
    check_usb()
    hdu.exec_process(['sudo', 'dmesg', '-c'], True)
    hdu.exec_process(['sudo', 'modprobe', 'usbmon'], True)
    

    conf_type = '---------- HIGH RES CHECK ----------'
    check_log.append('\n'+conf_type + '\n')
    thread_stop = False
    monitor_dmesg = Thread(target=check_dmesg_thread)
    monitor_dmesg.start()

    print(conf_type)
    print('Checking high-res data rates. This will take 30s...')
    target=create_config_target_hi_res()
    check_data_rate(target)
    check_throughput('/tmp/usbrate.txt',out_speed_thresh_high_res)

    conf_type = '---------- LOW RES CHECK ----------'
    check_log.append('\n'+conf_type + '\n')
    print(conf_type)
    print('Checking low-res data rates. This will take 30s...')
    target=create_config_target_low_res()
    check_data_rate(target)
    check_throughput('/tmp/usbrate.txt',out_speed_thresh_low_res)

    thread_stop = True
    monitor_dmesg.join()

    check_dmesg(dmesg_log)
    save_collected_log(check_log)

def check_install_usbtop():
    """
    Function to be executed at start. Checks for usbtop and if not prompts the user for installation.
    """
    out = Popen("which usbtop", shell=True, bufsize=64, stdin=PIPE, stdout=PIPE,close_fds=True).stdout.read()
    if len(out):
        return None
    else:
        print('"usbtop" tool is required to be installed for running this test first time.')
        x = raw_input('Enter "y" to proceed with Installation of "usbtop".\n')

        if x=='y' or x=='Y':
            script = 'cd ~/'
            script = script+';git clone https://github.com/aguinet/usbtop.git'
            script = script+';cd usbtop'
            script = script+';sudo apt install libboost-dev libpcap-dev libboost-thread-dev libboost-system-dev cmake'
            script = script+';mkdir _build && cd _build'
            script = script+';cmake -DCMAKE_BUILD_TYPE=Release ..'
            script = script+';make'
            script = script+';sudo make install'
            print('Installing usbtop tool.....')
            os.system(script)
            check = Popen("which usbtop", shell=True, bufsize=64, stdin=PIPE, stdout=PIPE,close_fds=True).stdout.read()
            if check:
                print(Fore.GREEN +'[Pass] "usbtop" sucessfully installed'+Style.RESET_ALL+'\n\n')
            else:
                print(Fore.RED + '[Fail] "usbtop" did not install.'+Style.RESET_ALL)
                sys.exit()
        else:
            print('Exiting...')
            sys.exit()

if args.f:
    log_file_path = args.f
    
if args.usb:
    get_usb_busID()
    check_usb()

if args.rate:
    check_rate_exec()

if args.scan_head:
    scan_head_check_rate()


