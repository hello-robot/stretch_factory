#!python


import sys
import time
import signal
import stretch_body.hello_utils as hello_utils
import threading

import stretch_body.base as base
import stretch_body.pimu as pimu


# ######## Modify These ###############


use_scope = False
if use_scope:
    import stretch_body.scope as scope
use_scope_deg =False

#scope_range = [-255,255]
#scope_data = 'effort'

scope_range = [-100, 100]
scope_data = 'err'

#scope_range = [0, 600]
#scope_data = 'debug'

#scope_range = [-3.5,3.5]
#scope_data = 'current'

#scope_range = [0,2000]
#scope_data = 'debug'
# #####################################


b=base.Base()
b.startup()

p=pimu.Pimu()
p.startup()

vd=b.params['motion']['slow']['vel_m']
ad=b.params['motion']['slow']['accel_m']
st=1.0
ff=0.0
contact_thresh_N=b.params['contact_thresh_N']

cycle_rate_hz = 0.2
target = [0.319185813604*.25, -0.319185813604*.25]
#target_vel=0.31918 #One rev per sec
#target_accel=0.31918 #On sec to get to one rev per sec
#target_rot_vel=2.024648357784478 #cause wheel to turn 1 rev /sec
if use_scope:
    s = scope.Scope(yrange=scope_range, title=scope_data)


class CycleThread(threading.Thread):
    def __init__(self,the_base, the_pimu):
        threading.Thread.__init__(self)
        self.the_base=the_base
        self.the_pimu=the_pimu
        self.titr = 0
        self.shutdown_flag = threading.Event()
    def run(self):
        print('Thread #%s started' % self.ident)
        tstart=time.time()

        self.the_base.pull_status()
        self.the_pimu.trigger_motor_sync()

        r1=hello_utils.rad_to_deg(self.the_base.status['right_wheel']['pos'])
        l1=hello_utils.rad_to_deg(self.the_base.status['left_wheel']['pos'])
        itr=0
        while not self.shutdown_flag.is_set():
            global vd
            tsleep=0.1
            nsleep = int((1 / cycle_rate_hz)/tsleep)

            self.titr = self.titr + 1
            # print 'Itr: ',self.titr, 'Duration: ',tstart-time.time(), 'X', self.the_base.status['x'], 'Y', self.the_base.status['y'], 'Theta', hello_utils.rad_to_deg(self.the_base.status['theta'])
            x_des = target[self.titr % 2]

            self.the_base.translate_by(x_m=x_des, v_m=vd, a_m=ad,contact_thresh_N=contact_thresh_N)
            itr=itr+1
            #if itr==4:
                #print 'Setting VD',vd
                #vd=.15
            #self.the_base.set_translate_velocity(v_m=target_vel,a_m=target_accel)
            #self.the_base.set_rotational_velocity(v_r=target_rot_vel, a_m=target_accel)
            self.the_base.push_command()
            self.the_pimu.trigger_motor_sync()


            for i in range(nsleep):
                time.sleep(tsleep)
                self.the_base.pull_status()
                #self.the_pimu.trigger_motor_sync()
                #r2 = hello_utils.rad_to_deg(self.the_base.status['right_wheel']['pos'])
                #l2 = hello_utils.rad_to_deg(self.the_base.status['left_wheel']['pos'])
                #xx = abs(l2 - l1) - abs(r2 - r1)
                #print 'xx',xx
                #s.step_display(xx)
                #print 'XX deg',xx
                if use_scope:
                    if not use_scope_deg:
                        s.step_display(self.the_base.status['right_wheel'][scope_data])
                    else:
                        s.step_display(hello_utils.rad_to_deg(self.the_base.status['left_wheel'][scope_data]))
                    #print 'V',self.the_base.status['x_vel']#'left_wheel']['vel']
        print('Thread #%s stopped' % self.ident)



# Register the signal handlers
signal.signal(signal.SIGTERM, hello_utils.thread_service_shutdown)
signal.signal(signal.SIGINT, hello_utils.thread_service_shutdown)
ct = CycleThread(b,p)
ct.setDaemon(True)
ct.start()

def menu():
    print '--------------'
    print 'm: menu'
    print 'p : set pKp_d : curr : ',b.left_wheel.gains['pKp_d']
    print 'i : set pKi_d : curr : ',b.left_wheel.gains['pKi_d']
    print 'd : set pKd_d : curr : ',b.left_wheel.gains['pKd_d']
    print 'l : set pKi_limit : curr : ',b.left_wheel.gains['pKi_limit']
    print 'v : set vel : curr : ',vd
    print 'a : set accel : curr : ',ad
    print 's : set stiffness : curr : ', st
    print 'f : set feedforward : curr : ', ff
    print 'm : set phase advance : curr : ', b.left_wheel.gains['phase_advance_d']
    print 'j : set iMax_pos: curr : ', b.left_wheel.gains['iMax_pos']
    print 'k : set iMax_neg: curr : ', b.left_wheel.gains['iMax_neg']
    print 'n : set contact_thresh_N: curr : ',contact_thresh_N
    print 'r : set cycle rate (Hz) : curr : ',cycle_rate_hz
    print 'A : set target A : curr : ',target[0]
    print 'B : set target B : curr : ',target[1]
    print 'w : write gains to YAML'
    print ''
    print 'Input?'


def step_interaction():
    global target, vd, ad, b,p,cycle_rate_hz, ff, st, contact_thresh_N
    menu()
    x=sys.stdin.readline()
    if len(x)>1:
        if x[0]=='p':
            b.left_wheel.gains['pKp_d']=float(x[1:])
            b.right_wheel.gains['pKp_d'] = float(x[1:])
        if x[0]=='i':
            b.left_wheel.gains['pKi_d']=float(x[1:])
            b.right_wheel.gains['pKi_d'] = float(x[1:])
        if x[0]=='d':
            b.left_wheel.gains['pKd_d']=float(x[1:])
            b.right_wheel.gains['pKd_d'] = float(x[1:])
        if x[0]=='l':
            b.left_wheel.gains['pKi_limit']=float(x[1:])
            b.right_wheel.gains['pKi_limit'] = float(x[1:])
        if x[0]=='v':
            vd = float(x[1:])
            print 'Setting vel to',vd
        if x[0]=='a':
            ad = float(x[1:])
        if x[0]=='s':
            st = float(x[1:])
        if x[0]=='f':
            ff = float(x[1:])
        if x[0]=='j':
            b.left_wheel.gains['iMax_pos'] = float(x[1:])
            b.right_wheel.gains['iMax_pos'] = float(x[1:])
        if x[0]=='k':
            b.left_wheel.gains['iMax_neg'] = float(x[1:])
            b.right_wheel.gains['iMax_neg'] = float(x[1:])
        if x[0]=='k':
            contact_thresh_N=float(x[1:])
        if x[0]=='m':
            b.left_wheel.gains['phase_advance_d'] = float(x[1:])
            b.right_wheel.gains['phase_advance_d'] = float(x[1:])
        if x[0]=='r':
            cycle_rate_hz = float(x[1:])
        if x[0]=='A':
            target[0] = float(x[1:])
        if x[0] == 'B':
            target[1] = float(x[1:])
        if x[0] == 'w':
            b.left_wheel.write_gains_to_YAML()
            b.right_wheel.write_gains_to_YAML()
        b.left_wheel.set_gains( b.left_wheel.gains)
        b.right_wheel.set_gains(b.right_wheel.gains)
    else:
        b.pretty_print()

try:
    while True:
        try:
            step_interaction()
        except (ValueError):
            print 'Bad input...'
except (KeyboardInterrupt, SystemExit, hello_utils.ThreadServiceExit):
    ct.shutdown_flag.set()
    ct.join()
    b.stop()
    p.stop()

