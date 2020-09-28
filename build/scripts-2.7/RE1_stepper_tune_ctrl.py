#!python


import sys
import time
import signal
import stretch_body.stepper as stepper
import stretch_body.hello_utils as hello_utils
import threading
import stretch_body.scope as scope


# ######## Modify These ###############


use_scope = True
use_scope_deg =False

#scope_range = [-255,255]
#scope_data = 'effort'

#scope_range = [-10, 10]
#scope_data = 'err'

#scope_range = [0, 600]
#scope_data = 'debug'

scope_range = [-3.5,3.5]
scope_data = 'current'

# #####################################

if len(sys.argv) < 2:
    raise Exception("Provide motor name e.g.: tune_stepper.py hello-motor1")
motor_name = sys.argv[1]

motor = stepper.Stepper('/dev/'+motor_name)
motor.startup()
motor.disable_sync_mode()
motor.push_command()
vd=motor.params['motion']['vel']
ad=motor.params['motion']['accel']
st=1.0
ff=0.0

cycle_rate_hz = 0.6
target = [10,45]
vel_target=-20

#motor.enable_pos_traj()
motor.enable_vel_traj()
if use_scope:
    s = scope.Scope(yrange=scope_range, title=scope_data)

class CycleThread(threading.Thread):
    def __init__(self,motor):
        threading.Thread.__init__(self)
        self.motor=motor
        self.titr = 0
        self.shutdown_flag = threading.Event()
    def run(self):
        print('Thread #%s started' % self.ident)
        tstart=time.time()
        while not self.shutdown_flag.is_set():
            ticks_per_cycle=50
            nsleep = int((1 / cycle_rate_hz)*ticks_per_cycle)
            for i in range(nsleep):
                time.sleep(1.0/ticks_per_cycle)
                motor.pull_status()
                if use_scope:
                    if not use_scope_deg:
                        s.step_display(motor.status[scope_data])
                    else:
                        s.step_display(hello_utils.rad_to_deg(motor.status[scope_data]))
                    #print 'Scope:',motor.status[scope_data]
            self.titr=self.titr+1
            print 'Itr: ',self.titr, 'Duration: ',tstart-time.time(), 'Pos', motor.status['pos']
            x_des=target[self.titr%2]
            print 'New Target: ',x_des
            #motor.set_command(x_des=x_des, v_des=vd, a_des=ad,stiffness=st,i_feedforward=ff)
            motor.set_command(v_des=vel_target)
            motor.push_command()
        print('Thread #%s stopped' % self.ident)



# Register the signal handlers
signal.signal(signal.SIGTERM, hello_utils.thread_service_shutdown)
signal.signal(signal.SIGINT, hello_utils.thread_service_shutdown)
ct = CycleThread(motor)
ct.setDaemon(True)
ct.start()

def menu():
    print '--------------'
    print 'm: menu'
    print 'p : set pKp_d : curr : ',motor.gains['pKp_d']
    print 'i : set pKi_d : curr : ',motor.gains['pKi_d']
    print 'd : set pKd_d : curr : ',motor.gains['pKd_d']
    print 'l : set pKi_limit : curr : ',motor.gains['pKi_limit']
    print 'z : set pLPF : curr: ', motor.gains['pLPF']
    print 'v : set vel : curr : ',vd
    print 'a : set accel : curr : ',ad
    print 's : set stiffness : curr : ', st
    print 'f : set feedforward : curr : ', ff
    print 'm : set phase advance : curr : ', motor.gains['phase_advance_d']
    print 'j : set iMax_pos: curr : ', motor.gains['iMax_pos']
    print 'k : set iMax_neg: curr : ', motor.gains['iMax_neg']
    print 'r : set cycle rate (Hz) : curr : ',cycle_rate_hz
    print 'A : set target A : curr : ',target[0]
    print 'B : set target B : curr : ',target[1]
    print 'w : write gains to YAML'
    print ''
    print 'Input?'


def step_interaction():
    global target, vd, ad, motor,cycle_rate_hz, ff, st
    menu()
    x=sys.stdin.readline()
    if len(x)>1:
        if x[0]=='p':
            motor.gains['pKp_d']=float(x[1:])
        if x[0]=='i':
            motor.gains['pKi_d']=float(x[1:])
        if x[0]=='d':
            motor.gains['pKd_d']=float(x[1:])
        if x[0]=='l':
            motor.gains['pKi_limit']=float(x[1:])
        if x[0]=='z':
            motor.gains['pLPF']=float(x[1:])
        if x[0]=='v':
            vd = float(x[1:])
        if x[0]=='a':
            ad = float(x[1:])
        if x[0]=='s':
            st = float(x[1:])
        if x[0]=='f':
            ff = float(x[1:])
        if x[0]=='j':
            motor.gains['iMax_pos'] = float(x[1:])
        if x[0]=='k':
            motor.gains['iMax_neg'] = float(x[1:])
        if x[0]=='m':
            motor.gains['phase_advance_d'] = float(x[1:])
        if x[0]=='r':
            cycle_rate_hz = float(x[1:])
        if x[0]=='A':
            target[0] = float(x[1:])
        if x[0] == 'B':
            target[1] = float(x[1:])
        if x[0] == 'w':
            motor.write_gains_to_YAML()
        motor.set_gains( motor.gains)
    else:
        motor.pretty_print()

try:
    while True:
        try:
            step_interaction()
        except (ValueError):
            print 'Bad input...'
        motor.pull_status()
except (KeyboardInterrupt, SystemExit, hello_utils.ThreadServiceExit):
    ct.shutdown_flag.set()
    ct.join()
    motor.stop()