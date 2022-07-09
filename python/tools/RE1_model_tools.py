
import sys
import stretch_body.stepper as stepper
import numpy as np
from numpy import linalg as LA
import matplotlib.pyplot as plt
import math



motor = stepper.Stepper('/dev/hello-motor-lift')

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
"""MOTOR MUST BE SET UP FIRST"""
def setup_current_model(self):
    A, b = self.get_least_squares_params()
    x = LA.lstsq(A.T, b, rcond=0)[0]
    self.model_coefficients = x

def get_least_squares_params(self):
    print("Starting data gathering")
    current_values = []
    velocity_mg_values = []
    acceleration_mg_values = []

    for destination in self.test_positions:
        print(destination)
        self.motor.pull_status()
        self.motor.set_command(x_des=destination)
        self.motor.push_command()

        # Gathering data while moving
        while not self.motor.status['near_pos_setpoint']:
            self.motor.pull_status()

            current_values.append(self.motor.status['current'])
            velocity_mg_values.append(self.motor.status['vel_mg'])
            acceleration_mg_values.append(self.motor.status['accel_mg'])

        # A rather hacky way to pause while still generating data
        t = 0
        while t < self.pause_time:
            self.motor.pull_status()

            current_values.append(self.motor.status['current'])
            velocity_mg_values.append(self.motor.status['vel_mg'])
            acceleration_mg_values.append(self.motor.status['accel_mg'])

            t = t + 1

    # velocity values and previous values
    A_list = [np.array(velocity_mg_values), np.array(acceleration_mg_values)]

    A = self.get_features(A_list)

    b = np.array(current_values)

    return A, b

def get_features(self, linear_features): ####NOTE THERE ARE FOUR FEATURES, SO STORE AS FOUR FLOATS################
    velocity = linear_features[0]
    acceleration = linear_features[1]
    A = np.vstack((np.ones((np.shape(velocity))), velocity,
                   np.sign(velocity) * (np.minimum(velocity * np.sign(acceleration), 0)),
                   np.sign(acceleration) * (np.minimum(acceleration * np.sign(velocity), 0))))
    return A

######################END MOTOR MODEL CODE########################################



######################START TORQUE MODEL CODE#####################################

"""Set up the coefficients with a few sweeps as usual"""
def setup_torque_model(self, end_positions):
    A, b = self.get_torque_params(end_positions)
    coefficients = self.get_torque_model(A, b)
    self.torque_coefficients = coefficients



"""Calculate the expected torque given the speed, current, and acceleration (sometimes?)"""
def calculate_expected_torque(self):
    assert self.torque_coefficients is not None
    self.motor.pull_status()
    current = self.motor.status['current']
    vel = self.motor.status['vel_mg']
    acc = self.motor.status['accel_mg']
    A_list = [np.array(vel), np.array(current), np.array(acc)]

    A = self.get_torque_features(A_list)

    return np.dot(A, self.torque_coefficients)




######################TORQUE MODEL UTILS#############################

"""Get the A and b by running motor a bunch of times, getting data, getting features from data, and turning into matrix"""
def get_torque_params(self, test_end_positions):
    print("Starting data gathering")
    current_values = []
    velocity_mg_values = []
    torque_values = []
    acc_values = []

    for destination in test_end_positions:
        print(destination)
        self.motor.pull_status()
        self.motor.set_command(x_des=destination)
        self.motor.push_command()

        while not self.motor.status['near_pos_setpoint']:
            self.motor.pull_status()
            current = self.motor.status['current']
            vel = self.motor.status['vel_mg']
            acc = self.motor.status['accel_mg']

            current_values.append(current)
            velocity_mg_values.append(vel)
            acc_values.append(acc)

            force = (self.grav + acc) * self.mass + self.velocity_friction_constant * np.sign(vel)
            torque = self.calculate_torque(force)
            torque_values.append(torque)

        t = 0
        while t < self.pause_time:
            self.motor.pull_status()
            current = self.motor.status['current']
            vel = self.motor.status['vel_mg']
            acc = self.motor.status['accel_mg']

            current_values.append(current)
            velocity_mg_values.append(vel)
            acc_values.append(acc)

            force = (self.grav + acc) * self.mass + self.velocity_friction_constant * np.sign(vel)
            torque = self.calculate_torque(force)
            torque_values.append(torque)

            t = t + 1

    # ax = plt.axes(projection='3d')
    # ax.scatter3D(velocity_mg_values, current_values, torque_values, c=torque_values)
    # plt.show()

    A_list = [np.array(velocity_mg_values), np.array(current_values), np.array(acc_values)]

    A = self.get_torque_features(A_list)

    b = np.array(torque_values)

    return A, b

"""Get possibly higher order features from linear features fed in (current_amplitude, temperature, current_frequency)"""
def get_torque_features(self, linear_features):
    # A = np.vstack((linear_features[0], linear_features[1]))
    velocity = linear_features[0]
    current = linear_features[1]
    acceleration = linear_features[2]

    A = np.vstack((np.ones((np.shape(velocity))), np.sign(velocity), current * np.sign(velocity),
                   np.square(current) * np.sign(velocity)))

    return A

"""Get the torque from the input force"""
def calculate_torque(self, force):
    return force * self.pulley_rad * self.gear_ratio

"""Solve least squares with A and b to get the x such that Ax - b is minimized in L2 norm (can change if needed?)"""
def get_torque_model(self, A, b):
    return LA.lstsq(A.T, b, rcond=0)[0]


if __name__ == "__main__":
    try:
        setup_motor()

        #TODO ADD ALL OTHER THINGS HERE

    except (KeyboardInterrupt, SystemExit):
        motor.stop()