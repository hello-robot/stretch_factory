#!/usr/bin/env python
import argparse
import stretch_body.head
import numpy as np
from stretch_body.hello_utils import *
import time

parser = argparse.ArgumentParser(
    description='Moves the head tilt/pan to different poses and calculates the average error of the positions '
                'reported by the Dynamixel Servos.')
parser.add_argument("--tilt", help="Tilt Control Error", action="store_true")
parser.add_argument("--pan", help="Pan Control Error", action="store_true")
parser.add_argument('-f', metavar='check_log_path', type=str,
                    help='The path to save Movement & Reported poses (default:/tmp/head_control_analyze.txt)')
args = parser.parse_args()
head_settling_delay = 0.8


def populate_given_head_poses(joint_name):
    N = 10
    if joint_name == 'head_tilt':
        return np.linspace(0, -90, N)
    if joint_name == 'head_pan':
        return np.linspace(0, -180, N)


def collect_data_analyze(joint_name):
    given_head_poses = populate_given_head_poses(joint_name)
    collected_head_poses = []
    head_poses_error = []

    h = stretch_body.head.Head()
    h.startup()
    print('Moving {} to different poses.'.format(joint_name))
    print('============================\n\n\n')

    for pose in given_head_poses:
        print('Move to : {} deg'.format(pose))
        h.move_to(joint_name, deg_to_rad(pose))
        time.sleep(head_settling_delay)
        h.pull_status()
        status = h.status
        reported_pos = rad_to_deg(status[joint_name]['pos'])
        print('Reported pos : {} deg'.format(reported_pos))
        print('\n\n')
        collected_head_poses.append(reported_pos)
        head_poses_error.append(abs(reported_pos - pose))

    time.sleep(head_settling_delay)
    h.pose('ahead')

    head_poses_error = np.array(head_poses_error)
    average_error = float(np.sum(head_poses_error) / len(head_poses_error))

    print('Average "{}" Pose Error(deg) : {}'.format(joint_name, average_error))
    max_in = np.argmax(head_poses_error)
    print('Maximum Error(deg) : {} when move_to({} deg)'.format(head_poses_error[max_in], given_head_poses[max_in]))


if args.tilt:
    collect_data_analyze('head_tilt')

if args.pan:
    collect_data_analyze('head_pan')
