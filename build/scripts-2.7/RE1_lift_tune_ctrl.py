#!python


import sys, tty, termios
import threading
import time
import signal
import stretch_body.hello_utils as hello_utils
import threading

import stretch_body.lift as lift
import stretch_body.pimu as pimu


# ######## Modify These ###############


use_scope = True
if use_scope:
    import scope
use_scope_deg =False

#scope_range = [-300, 300]
#scope_data = 'pos'

#scope_range = [-10, 10]
#scope_data = 'err'

#scope_range = [0, 600]
#scope_data = 'debug'

#scope_range = [-3.5,3.5]
#scope_data = 'current'
scope_range = [-40,100]
scope_data = 'force'
#scope_range = [-1,100]
#scope_range = [0,2000]
#scope_data = 'debug'
# #####################################


l=lift.Lift()
l.startup()

use_pimu=True

if use_pimu:
    p=pimu.Pimu()
    p.startup()
else:
    p=None
vd=l.params['motion']['med']['vel_m']*1.5
ad=l.params['motion']['med']['accel_m']*1.5
st=1.0
i_ff=l.params['i_feedforward']
down_N = l.params['contact_thresh_N'][0]
up_N = l.params['contact_thresh_N'][1]


cycle_rate_hz = 0.5
#target = [0, 1.1]
target = [-.2,.2]


if use_scope:
    s = scope.Scope(yrange=scope_range, title=scope_data)

class CycleThread(threading.Thread):
    def __init__(self,the_lift, the_pimu):
        threading.Thread.__init__(self)
        self.the_lift=the_lift
        self.the_pimu=the_pimu
        self.titr = 0
        self.shutdown_flag = threading.Event()
    def run(self):
        print('Thread #%s started' % self.ident)
        tstart=time.time()
        gl_last=0
        while not self.shutdown_flag.is_set():
            self.the_lift.pull_status()
            if use_pimu:
                self.the_pimu.trigger_motor_sync()

            tsleep=0.1
            nsleep = int((1 / cycle_rate_hz)/tsleep)
            #print 'New Itr'
            self.titr = self.titr + 1
            # print 'Itr: ',self.titr, 'Duration: ',tstart-time.time(), 'X', self.the_lift.status['x'], 'Y', self.the_lift.status['y'], 'Theta', hello_utils.rad_to_deg(self.the_lift.status['theta'])
            x_des = target[self.titr % 2]
            self.the_lift.move_by(x_m=x_des, v_m=vd, a_m=ad, stiffness=st,  contact_thresh_pos_N=up_N, contact_thresh_neg_N=down_N,req_calibration=False)
            #self.the_lift.move_to(x_m=x_des, v_m=vd, a_m=ad, stiffness=st, contact_thresh_pos_N=up_N,contact_thresh_neg_N=down_N, req_calibration=False)
            self.the_lift.push_command()
            if use_pimu:
                self.the_pimu.trigger_motor_sync()


            for i in range(nsleep):
                time.sleep(tsleep)
                self.the_lift.pull_status()
                if use_pimu:
                    self.the_pimu.trigger_motor_sync()

                if use_scope:
                    if not use_scope_deg:
                        s.step_display(self.the_lift.status[scope_data])
                    else:
                        s.step_display(hello_utils.rad_to_deg(self.the_lift.motor.status[scope_data]))
                    #print hello_utils.rad_to_deg(self.the_lift.motor.status[scope_data])
        print('Thread #%s stopped' % self.ident)



# Register the signal handlers
signal.signal(signal.SIGTERM, hello_utils.thread_service_shutdown)
signal.signal(signal.SIGINT, hello_utils.thread_service_shutdown)
ct = CycleThread(l,p)
ct.setDaemon(True)
ct.start()



def menu():
    print '--------------'
    print 'm: menu'
    print 'p : set pKp_d : curr : ',l.motor.gains['pKp_d']
    print 'i : set pKi_d : curr : ',l.motor.gains['pKi_d']
    print 'd : set pKd_d : curr : ',l.motor.gains['pKd_d']
    print 'l : set pKi_limit : curr : ',l.motor.gains['pKi_limit']
    print 'v : set vel : curr : ',vd
    print 'a : set accel : curr : ',ad
    print 's : set stiffness : curr : ', st
    print 'f : set i_feedforward : curr : ', i_ff
    print 'm : set phase advance : curr : ', l.motor.gains['phase_advance_d']
    print 'j : set iMax_pos: curr : ', l.motor.gains['iMax_pos']
    print 'k : set iMax_neg: curr : ', l.motor.gains['iMax_neg']
    print 'n : set contact_thresh_N up: curr : ', up_N
    print 'o : set contact_thresh_N down: curr : ', down_N
    print 'r : set cycle rate (Hz) : curr : ',cycle_rate_hz
    print 'A : set target A : curr : ',target[0]
    print 'B : set target B : curr : ',target[1]
    print 'w : write gains to YAML'
    print ''
    print 'Input?'


def step_interaction():
    global target, vd, ad, b,p,cycle_rate_hz, i_ff, st, up_N, down_N
    menu()
    x=sys.stdin.readline()
    if len(x)>1:
        if x[0]=='p':
            l.motor.gains['pKp_d']=float(x[1:])
        if x[0]=='i':
            l.motor.gains['pKi_d']=float(x[1:])
        if x[0]=='d':
            l.motor.gains['pKd_d']=float(x[1:])
        if x[0]=='l':
            l.motor.gains['pKi_limit']=float(x[1:])
        if x[0]=='v':
            vd = float(x[1:])
        if x[0]=='a':
            ad = float(x[1:])
        if x[0]=='s':
            st = float(x[1:])
        if x[0]=='f':
            i_ff = float(x[1:])
        if x[0]=='j':
            l.motor.gains['iMax_pos'] = float(x[1:])
        if x[0]=='k':
            l.motor.gains['iMax_neg'] = float(x[1:])
        if x[0]=='n':
            up_N=float(x[1:])
        if x[0]=='o':
            down_N = float(x[1:])
        if x[0]=='m':
            l.motor.gains['phase_advance_d'] = float(x[1:])
        if x[0]=='r':
            cycle_rate_hz = float(x[1:])
        if x[0]=='A':
            target[0] = float(x[1:])
        if x[0] == 'B':
            target[1] = float(x[1:])
        if x[0] == 'w':
            l.motor.write_gains_to_YAML()
        l.motor.set_gains(l.motor.gains)
    else:
        l.pretty_print()

try:
    while True:
        try:
            step_interaction()
        except (ValueError):
            print 'Bad input...'
        #l.step()
except (KeyboardInterrupt, SystemExit, hello_utils.ThreadServiceExit):
    ct.shutdown_flag.set()
    ct.join()
    l.stop()
    p.stop()
