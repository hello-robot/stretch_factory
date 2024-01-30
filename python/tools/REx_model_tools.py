#!/usr/bin/env python3
import sys
import stretch_body.stepper as stepper
import numpy as np
from numpy import linalg as LA
import matplotlib.pyplot as plt
import math

GRAVITY = 9.81
VELOCITY_FRICTION_CONST = 100

# This should be full runs from top to bottom
test_positions = [0, 50, 0, 100, 50, 0, 25, 0]

# TODO These should be data gathered from the yaml file (or elsewhere?)
pulley_rad = 1
gear_ratio = 1
mass = 1

# This is the arbitrary pause time (in clock cycles)
pause_time = 2000

def setup_motor():
    # Setup

    motor.startup()
    motor.disable_sync_mode()
    motor.disable_runstop()
    motor.push_command()

    motor.enable_pos_traj()
    # motor.enable_freewheel()
    # motor.enable_pos_pid()
    motor.push_command()
    print('setup complete')



#######################START MOTOR MODEL CODE#########################

"""Call setup_current_model when motor is on in order to run sweeps and get coefficients for model"""
def setup_current_model():
    A, b = get_current_params()
    x = LA.lstsq(A.T, b, rcond=0)[0]
    return x

def get_current_params():
    print("Starting data gathering")
    current_values = []
    velocity_mg_values = []
    acceleration_mg_values = []

    for destination in test_positions:
        print(destination)
        motor.pull_status()
        motor.set_command(x_des=destination)
        motor.push_command()

        # Gathering data while moving
        while not motor.status['near_pos_setpoint']:
            motor.pull_status()

            current_values.append(motor.status['current'])
            velocity_mg_values.append(motor.status['vel_mg'])
            acceleration_mg_values.append(motor.status['accel_mg'])

        # A rather hacky way to pause while still generating data
        t = 0
        while t < pause_time:
            motor.pull_status()

            current_values.append(motor.status['current'])
            velocity_mg_values.append(motor.status['vel_mg'])
            acceleration_mg_values.append(motor.status['accel_mg'])

            t = t + 1

    # velocity values and previous values
    A_list = [np.array(velocity_mg_values), np.array(acceleration_mg_values)]

    A = get_current_features(A_list)

    b = np.array(current_values)

    return A, b

def get_current_features(linear_features): ####NOTE THERE ARE FOUR FEATURES, SO STORE AS FOUR FLOATS################
    velocity = linear_features[0]
    acceleration = linear_features[1]
    """
    A = np.vstack((np.ones((np.shape(velocity))), velocity,
                   np.sign(velocity) * (np.minimum(np.exp(velocity) * np.sign(acceleration), 0)),
                   np.sign(acceleration) * (np.minimum(np.exp(acceleration) * np.sign(velocity), 0))))

    """
    A = np.vstack((np.ones((np.shape(velocity))), velocity,
               np.sign(velocity) * (np.minimum(velocity * np.sign(acceleration), 0)),
               np.sign(acceleration) * (np.minimum(acceleration * np.sign(velocity), 0))))
    


    return A

######################END MOTOR MODEL CODE########################################



######################START TORQUE MODEL CODE#####################################

"""Set up the coefficients with a few sweeps as usual"""
def setup_torque_model():
    A, b = get_torque_params()
    x = LA.lstsq(A.T, b, rcond=0)[0]
    return x

"""Get the A and b by running motor a bunch of times, getting data, getting features from data, and turning into matrix"""
def get_torque_params():
    print("Starting data gathering")
    current_values = []
    velocity_mg_values = []
    torque_values = []
    acc_values = []

    for destination in test_positions:
        print(destination)
        motor.pull_status()
        motor.set_command(x_des=destination)
        motor.push_command()

        while not motor.status['near_pos_setpoint']:
            motor.pull_status()
            current = motor.status['current']
            vel = motor.status['vel_mg']
            acc = motor.status['accel_mg']

            current_values.append(current)
            velocity_mg_values.append(vel)
            acc_values.append(acc)

            force = (GRAVITY + acc) * mass + VELOCITY_FRICTION_CONST * np.sign(vel)
            torque = calculate_torque(force)
            torque_values.append(torque)

        t = 0
        while t < pause_time:
            motor.pull_status()
            current = motor.status['current']
            vel = motor.status['vel_mg']
            acc = motor.status['accel_mg']

            current_values.append(current)
            velocity_mg_values.append(vel)
            acc_values.append(acc)

            force = (GRAVITY + acc) * mass + VELOCITY_FRICTION_CONST * np.sign(vel)
            torque = calculate_torque(force)
            torque_values.append(torque)

            t = t + 1

    # ax = plt.axes(projection='3d')
    # ax.scatter3D(velocity_mg_values, current_values, torque_values, c=torque_values)
    # plt.show()

    A_list = [np.array(velocity_mg_values), np.array(current_values), np.array(acc_values)]

    A = get_torque_features(A_list)

    b = np.array(torque_values)

    return A, b

"""Get possibly higher order features from linear features fed in (current_amplitude, temperature, current_frequency)"""
def get_torque_features(linear_features):
    # A = np.vstack((linear_features[0], linear_features[1]))
    velocity = linear_features[0]
    current = linear_features[1]
    acceleration = linear_features[2]

    A = np.vstack((np.ones((np.shape(velocity))), np.sign(velocity), current * np.sign(velocity),
                   np.square(current) * np.sign(velocity)))

    return A

"""Get the torque from the input force"""

def calculate_torque(force):
    return force * pulley_rad * gear_ratio


"""Calculate the expected torque given the speed, current, and acceleration (WRONG FILE)"""
#TODO put this function elsewhere where it would be used to calculate the expected torque (doesn't belong in the tool)
#TODO needs to get the coefficients from YAML file (torque_coefficients needs to be a np array perhaps constructed from YAML params)
def calculate_expected_torque():
    assert torque_coefficients is not None
    motor.pull_status()
    current = motor.status['current']
    vel = motor.status['vel_mg']
    acc = motor.status['accel_mg']
    A_list = [np.array(vel), np.array(current), np.array(acc)]

    A = get_torque_features(A_list)

    return np.dot(A, torque_coefficients)




"""Input arguments are the motor name (just this for now, change?)"""
if __name__ == "__main__":

    print('This tool is no longer maintained. It is kept for reference only.')
    exit(1)

    if len(sys.argv) < 2:
        raise Exception("Provide motor name e.g.: stepper_jog.py hello-motor1")
    motor_name = sys.argv[1]
    print(motor_name)
    # '/dev/hello-motor-lift' in testing

    mode = int(sys.argv[2])
    # 0 for current model setup, 1 for torque model setup

    motor = stepper.Stepper('/dev/'+motor_name)


    try:
        setup_motor()

        if mode == 0:
            current_coefficients = setup_current_model()
            print(current_coefficients)
            #TODO write current coefficients to yaml?
        elif mode == 1:
            torque_coefficients = setup_torque_model()
            #TODO what to do with them now?
        else:
            raise Exception("mode must be 0 or 1")

    except (KeyboardInterrupt, SystemExit):
        motor.stop()