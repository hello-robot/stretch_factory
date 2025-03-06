#!/usr/bin/python3
from dataclasses import asdict, dataclass
from enum import IntEnum
import json
import os
import subprocess

from stretch_body.hello_utils import *
import argparse
import click

from stretch_body.pimu import Pimu
from stretch_body.lift import Lift
from stretch_body.arm import Arm
from stretch_body.prismatic_joint import PrismaticJoint

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

import logging

# Configure logging to output to the console
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

class StepCalibrationResult(IntEnum):
    TARGETS_NOT_REACHED = 0
    FIRST_OVERSHOOT = 1  # Capturing this may help debug bad overshooting behavior
    BACKTRACKING_DECREASING_TIME = 2
    BACKTRACKING_INCREASING_TIME = 3
    TARGET_REACHED = 4
    TARGET_REACHED_JUST_DOING_MOTION = 5

@dataclass
class CalibrationResults:
    effort_pct_pos: tuple[float, float, float, float]
    effort_pct_neg: tuple[float, float, float, float]
    pos_out: tuple[float, float, float, float]
    pos_in: tuple[float, float, float, float]
    max_effort_pct_pos: float
    min_effort_pct_neg: float


@dataclass
class BatteryInfo:
    battery_voltage: float
    battery_percentage: float

    def __repr__(self) -> str:
        return f"Battery Level: {self.battery_voltage}V ({self.battery_percentage}%)"

    def to_json(self):
        return json.loads(json.dumps(asdict(self)))

    @staticmethod
    def get_battery_info(pimu:Pimu, max_battery_volage: float = 14.5):

        pimu.pull_status()
        battery_voltage = pimu.status["voltage"]
        battery_voltage = round(battery_voltage, 2)
        battery_percentage: float = battery_voltage / max_battery_volage * 100
        battery_percentage = round(battery_percentage)

        return BatteryInfo(
            battery_voltage=battery_voltage, battery_percentage=battery_percentage
        )


@dataclass
class CalibrationTargets:
    """
    Calibration conditions, see `MotionData::is_calibrated()` for more info
    """

    effort_percent_target: float  # We want to reach this target and stop
    goal_error_absolute_target_cm: float  # cm deviation from the trajectory
    goal_error_percentage_target: float  # % deviation from the trajectory goal

    travel_duration_start_seconds: float  # seconds, start slow
    travel_duration_decrement_by_max_seconds: (
        float  # seconds, maximum we can decrease duration by.
    )


    offset_from_joint_limit_min: float
    offset_from_joint_limit_max: float

    @staticmethod
    def _shared_defaults(travel_duration_start_seconds:float,travel_duration_decrement_by_max_seconds:float ):
        return CalibrationTargets(
            effort_percent_target=80,
            goal_error_absolute_target_cm=1.2,
            goal_error_percentage_target=10.0,
            offset_from_joint_limit_min = 0.2,
            offset_from_joint_limit_max = 0.2,
            travel_duration_start_seconds=travel_duration_start_seconds,
            travel_duration_decrement_by_max_seconds=travel_duration_decrement_by_max_seconds,
        )
        
    
    @staticmethod
    def linear_default():
        return CalibrationTargets._shared_defaults(
            travel_duration_start_seconds=9.0,
            travel_duration_decrement_by_max_seconds=3.5,
        )

    @staticmethod
    def cubic_default():
        return CalibrationTargets._shared_defaults(
            travel_duration_start_seconds=10.0,
            travel_duration_decrement_by_max_seconds=3.0,
        )

    @staticmethod
    def quintic_default():
        return CalibrationTargets._shared_defaults(
            travel_duration_start_seconds=12.0,
            travel_duration_decrement_by_max_seconds=3.0
        )


class MotionData:
    """
    Keeps track of timestamps, joint positions, and motor efforts during motion.

    Provides a `collect_data()` method to sample data.
    """

    def __init__(
        self,
        trajectory: "TrajectoryFlattened",
        calibration_targets: "CalibrationTargets",
        timestamps_during_motion: list[float] | None = None,
        positions_during_motion: list[float] | None = None,
        velocities_during_motion: list[float] | None = None,
        effort_during_motion: list[float] | None = None,
        current_during_motion: list[float] | None = None,
        step_calibration_result: "StepCalibrationResult|None" = None,
    ) -> None:
        self.timestamps_during_motion = timestamps_during_motion or []
        self.positions_during_motion = positions_during_motion or []
        self.velocities_during_motion = velocities_during_motion or []
        self.effort_during_motion = effort_during_motion or []
        self.current_during_motion = current_during_motion or []

        self.trajectory: TrajectoryFlattened = trajectory
        self.calibration_targets = calibration_targets

        self.step_calibration_result = step_calibration_result

        self.is_motion_stopped_for_safety = False

    def motion_overview(self, prefix: str = ""):
        warnings = ""
        if not np.isclose(
            self.goal_position_cm,
            self.actual_position_cm,
            atol=self.calibration_targets.goal_error_absolute_target_cm,
        ):
            warnings += f"WARNING: the {joint.name} did not reach the goal.\n"
            
        if self.is_motion_stopped_for_safety:
            warnings += f"WARNING: the {joint.name}'s motion was stopped for safety before completing the trajectory.\n"

        return f"""{prefix}
    Moved {self.travel_range_cm}cm in {self.trajectory.travel_duration_seconds} seconds ({self.linear_speed_cm_per_second})cm/s. 
    Average effort: {self.effort_percent_average_last_10_readings}%, Abs Max Effort: {self.effort_percent_max_absolute}, Max effort: {self.effort_percent_max}% , Min effort: {self.effort_percent_min}%
    Goal Position: {self.goal_position_cm}cm. Sampled Position: {self.actual_position_cm}cm. Error: {self.error_percent}% ({self.error_absolute_cm}cm)
    Target effort reached? {self.is_exceeds_effort_target()} 
    Target absolute goal position error reached? {self.is_exceeds_absolute_goal_error_target()}
    Target percentage goal position error reached? {self.is_exceeds_percent_goal_error_target()}
    {warnings}
"""

    @property
    def timestamps_normalized(self):

        return np.subtract(
            self.timestamps_during_motion, np.min(self.timestamps_during_motion)
        )

    @property
    def positions_cm(self):
        return np.round(np.multiply(self.positions_during_motion, 100), 2)

    @property
    def accelerations(self):
        timestamps_normalized = self.timestamps_normalized

        accelerations = np.diff(self.velocities_during_motion) / np.diff(
            timestamps_normalized
        )

        # To match the lengths for plotting, average timestamps between each pair of points:
        acceleration_times = (
            np.add(timestamps_normalized[:-1], timestamps_normalized[1:])
        ) / 2

        return (accelerations, acceleration_times)

    def collect_data(self, joint: PrismaticJoint):
        self.timestamps_during_motion.append(time.time())
        self.positions_during_motion.append(joint.status["pos"])
        self.velocities_during_motion.append(joint.status["vel"])
        self.effort_during_motion.append(joint.motor.status["effort_pct"])
        self.current_during_motion.append(joint.motor.status["current"])

    def is_exceeds_effort_target(self):
        return self.effort_percent_max_absolute >= self.calibration_targets.effort_percent_target

    def is_exceeds_absolute_goal_error_target(self):
        return (
            self.error_absolute_cm
            >= self.calibration_targets.goal_error_absolute_target_cm
        )

    def is_exceeds_percent_goal_error_target(self):
        return (
            self.error_percent >= self.calibration_targets.goal_error_percentage_target
        )

    def is_exceeded_calibration_targets(self):
        """
        Trajectory joint calibration is considered complete when ONE of these conditions are satisfied:
        1. Joint effort > EFFORT_TARGET (80%).
        2. Position % error from the trajectory goal is > 50%.
        3. Absolute Position error from the trajectory goal is > MAX_ABSOLUTE_GOAL_ERROR (3cm).
        """
        return (
            self.is_exceeds_effort_target()
            or self.is_exceeds_absolute_goal_error_target()
            or self.is_exceeds_percent_goal_error_target()
        )

    def current_linear_speed_meters_per_second(self, is_round: bool = True):
        speed = (
            self.trajectory.trajectory_range / self.trajectory.travel_duration_seconds
        )
        return round(speed, 2) if is_round else speed

    def _to_cm(self, value: float):
        return round(value * 100, 2)

    @property
    def goal_position_cm(self):
        return self._to_cm(self.trajectory.positions[-1])

    @property
    def actual_position_cm(self):
        return self.positions_cm[-1]

    @property
    def error_absolute_cm(self):
        return round(abs(self.goal_position_cm - self.actual_position_cm), 2)

    @property
    def error_percent(self):
        return round(self.error_absolute_cm / self.goal_position_cm * 100, 2)

    @property
    def effort_percent_average_last_10_readings(self):
        return round(float(np.average(np.abs(self.effort_during_motion[-10:]))), 2)

    @property
    def effort_percent_max_absolute(self):
        # Take the max of both negative and positive efforts:
        return float(
            np.max(
            (np.max(self.effort_percent_max),
            np.abs(self.effort_percent_min))
            )
            )
    
    @property
    def effort_percent_max(self):
        return round(float(np.max(self.effort_during_motion)),2)
    
    @property
    def effort_percent_min(self):
        return round(float(np.min(self.effort_during_motion)),2)

    @property
    def linear_speed_cm_per_second(self):
        return self._to_cm(self.current_linear_speed_meters_per_second(is_round=False))

    @property
    def travel_range_cm(self):
        return self._to_cm(self.trajectory.trajectory_range)

    def to_json(self):
        return json.loads(
            json.dumps(
                {
                    "timestamps_during_motion": self.timestamps_during_motion,
                    "positions_during_motion": self.positions_during_motion,
                    "velocities_during_motion": self.velocities_during_motion,
                    "effort_during_motion": self.effort_during_motion,
                    "current_during_motion": self.current_during_motion,
                    "positions_cm": self.positions_cm.tolist(),
                    "accelerations": self.accelerations[0].tolist(),
                    "step_calibration_result": self.step_calibration_result,
                    "trajectory": self.trajectory.to_json(),
                    "calibration_targets": asdict(self.calibration_targets),
                }
            )
        )

    @staticmethod
    def from_json(json_data: dict):
        return MotionData(
            trajectory=TrajectoryFlattened(**json_data["trajectory"]),
            calibration_targets=CalibrationTargets(**json_data["calibration_targets"]),
            timestamps_during_motion=json_data["timestamps_during_motion"],
            positions_during_motion=json_data["positions_during_motion"],
            velocities_during_motion=json_data["velocities_during_motion"],
            effort_during_motion=json_data["effort_during_motion"],
            current_during_motion=json_data["current_during_motion"],
            step_calibration_result= StepCalibrationResult(json_data["step_calibration_result"]) if json_data["step_calibration_result"] else None,
        )


@dataclass
class TrajectoryFlattened:
    """
    Definition of a waypoint trajectory - flattened so that indecies correspond to the waypoint number. e.g. index 0 is the first waypoint.
    """

    timestamps: list[float]
    positions: list[float]
    velocities: list[float] | None
    accelerations: list[float] | None

    def to_json(self):
        return json.loads(
            json.dumps(
                {
                    "timestamps": self.timestamps,
                    "positions": self.positions,
                    "velocities": self.velocities,
                    "accelerations": self.accelerations,
                }
            )
        )

    @property
    def travel_duration_seconds(self):
        return abs(self.timestamps[-1] - self.timestamps[0])

    @property
    def trajectory_range(self):
        return abs(self.positions[-1] - self.positions[0])


def plot_motion_profiles_and_save_outputs(
    calibration_data: "TrajectoryCalibrationData",
    motion_data:"MotionData",
    filename_prefix: str = "",
    write_to_json=True,
    show_plot=False,
):
    """
    Plot the motion profiles and joint effort. 
    Also saves the plots and a JSON file of the calibration data.
    """

    trajectory = motion_data.trajectory

    waypoints_time = trajectory.timestamps
    waypoints_position = trajectory.positions
    waypoints_velocity = trajectory.velocities
    waypoints_acceleration = trajectory.accelerations

    # Plotting the data
    plt.close()
    fig = plt.figure(figsize=(12, 25))
    loc = "lower center"
    bbox_to_anchor = (1.1, -0.20)
    ncol = 1

    # Plot Position vs Time
    plt.subplot(4, 1, 1)
    plt.plot(
        motion_data.timestamps_normalized,
        motion_data.positions_cm,
        label="Sampled",
        color="b",
    )
    if waypoints_position:
        plt.plot(
            waypoints_time,
            np.multiply(waypoints_position, 100),
            "gx",
            label="Trajectory",
        )
    plt.xlabel("Time (s)")
    plt.ylabel("Position (cm)")
    plt.title("Position vs Time")
    plt.xlim((waypoints_time[0] - 0.1, waypoints_time[-1] + 0.1))
    plt.legend(loc=loc, bbox_to_anchor=bbox_to_anchor, ncol=ncol)
    plt.grid(True)

    # Plot Velocity vs Time
    plt.subplot(4, 1, 2)
    plt.plot(
        motion_data.timestamps_normalized,
        np.multiply(motion_data.velocities_during_motion, 100),
        label="Sampled",
        color="g",
    )
    if waypoints_velocity:
        plt.plot(waypoints_time, waypoints_velocity, "gx", label="Trajectory")
    plt.xlabel("Time (s)")
    plt.ylabel("Velocity (cm/s)")
    plt.title("Velocity vs Time")
    plt.xlim((waypoints_time[0] - 0.1, waypoints_time[-1] + 0.1))
    plt.legend(loc=loc, bbox_to_anchor=bbox_to_anchor, ncol=ncol)
    plt.grid(True)

    # Plot Acceleration vs Time
    (accelerations, acceleration_times) = motion_data.accelerations
    plt.subplot(4, 1, 3)
    plt.plot(
        acceleration_times, np.multiply(accelerations, 100), label="Sampled", color="k"
    )
    if waypoints_acceleration:
        plt.plot(waypoints_time, waypoints_acceleration, "gx", label="Trajectory")
    plt.xlabel("Time (s)")
    plt.ylabel("Acceleration (cm/s²)")
    plt.title("Acceleration vs Time")
    plt.xlim((waypoints_time[0] - 0.1, waypoints_time[-1] + 0.1))
    plt.legend(loc=loc, bbox_to_anchor=bbox_to_anchor, ncol=ncol)
    plt.grid(True)

    # Plot Efforts vs Time
    ax = plt.subplot(4, 1, 4)
    efforts = motion_data.effort_during_motion
    plt.plot(motion_data.timestamps_normalized, efforts, label="Sampled", color="r")
    plt.text(0, 1.05, f"{calibration_data.battery_info}", transform=ax.transAxes)
    plt.xlabel("Time (s)")
    plt.ylabel("Effort (%)")
    plt.title("Efforts and Current vs Time")
    plt.tick_params(axis="y", labelcolor="red")
    plt.xlim((waypoints_time[0] - 0.1, waypoints_time[-1] + 0.1))
    plt.legend(loc=loc, bbox_to_anchor=bbox_to_anchor, ncol=ncol)
    plt.grid(True)
    # Create the secondary y-axis for current:
    ax2 = ax.twinx()
    ax2.plot(
        motion_data.timestamps_normalized,
        motion_data.current_during_motion,
        color="blue",
    )
    ax2.set_ylabel("Amps (A)", color="blue")
    ax2.tick_params(axis="y", labelcolor="blue")

    # Display the plots
    fig.suptitle(
        f"{calibration_data.profile_name} Motion Profile Data for {calibration_data.description} {motion_data.linear_speed_cm_per_second}cm/s"
    )
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    if show_plot:
        matplotlib.use(
            "TKAgg"
        )  # Makes headless/remote connection plotting possible with an Xvfb display.

        plt.show(block=False)

    # Save data
    title_snakecase = f"{filename_prefix}{calibration_data.description}_{calibration_data.profile_name}_{motion_data.linear_speed_cm_per_second}cm/s"
    title_snakecase = title_snakecase.replace(" ", "_").replace("/", "_per_").lower()

    if (
        motion_data.is_motion_stopped_for_safety
    ):
        title_snakecase += "_stopped_for_safety"

    if (
        motion_data.step_calibration_result
        == StepCalibrationResult.FIRST_OVERSHOOT
    ):
        title_snakecase += "_first_overshoot"

    global trajectory_folder_to_save_plots
    if write_to_json:
        filename = f"{trajectory_folder_to_save_plots}/{title_snakecase}.json"
        with open(filename, "w") as json_file:
            json.dump(calibration_data.to_json(), json_file, indent=4)

    plt.savefig(f"{trajectory_folder_to_save_plots}/{title_snakecase}.png")


def _run_profile_trajectory(
    joint: PrismaticJoint,
    trajectory: TrajectoryFlattened,
    calibration_targets: CalibrationTargets,
):
    """
    Follows a trajectory and captures position and effort data.

    This monitors joint effort and calls `joint.motor.enable_safety()` if the effort exceeds a threshold.

    Call `_set_trajectory_based_on_joint_limits()` before calling this.
    """
    motion_data = MotionData(
        trajectory=trajectory, calibration_targets=calibration_targets
    )

    if len(joint.trajectory.waypoints) == 0:
        raise Exception(
            "No waypoints. Did you call _set_trajectory_based_on_joint_limits()?"
        )

    joint.motor.disable_sync_mode()  # this is important for trajectory mode to move joints.

    joint.motor.disable_guarded_mode()

    # We're disabling the limits for dynamic checks.
    joint.params['motion']['trajectory_max']['vel_m'] = 0.5
    joint.params['motion']['trajectory_max']['accel_m'] = 0.5

    joint.pull_status()

    time.sleep(1) # let things settle

    assert joint.follow_trajectory(
        move_to_start_point=True
    ), "Setting trajectory failed."

    time.sleep(0.25)
    joint.pull_status()
    joint.update_trajectory()
    joint.pull_status()
    SAMPLING_RATE_HZ = 10
    while joint.get_trajectory_time_remaining() != 0:
        time.sleep(1/SAMPLING_RATE_HZ)  # Sample at 1/SAMPLING_RATE seconds

        joint.pull_status()
        joint.update_trajectory()

        motion_data.collect_data(joint=joint)

        if abs(motion_data.effort_during_motion[-1]) > motion_data.calibration_targets.effort_percent_target:
            # Effort too high!
            print(f"Effort exceeded, telling {joint.name} to stop!")
            joint.motor.enable_safety()
            joint.push_command()
            joint.stop_trajectory()
            joint.push_command()
            joint.pull_status()

            motion_data.is_motion_stopped_for_safety = True

            break
        

    return motion_data


def _set_trajectory_based_on_joint_limits(
    joint: PrismaticJoint,
    is_positive_direction: bool,
    travel_duration: float,
    is_use_velocity: bool,
    is_use_acceleration: bool,
    offset_from_joint_limit_min: float,
    offset_from_joint_limit_max: float
):
    """
    Sets the starting and ending positions to the range limits of the joint.

    If `is_use_velocity` is true, the velocity steps will be set to 0 m/s at either extremes.
    If `is_use_acceleration` is true, the acceleration steps will be set to 0 m/s^2 at either extremes.

    returns `joint_range`
    """
    joint_max_position = joint.params["range_m"][1] - offset_from_joint_limit_max
    joint_min_position = joint.params["range_m"][0] + offset_from_joint_limit_min

    start_position = joint_min_position if is_positive_direction else joint_max_position
    end_position = joint_max_position if is_positive_direction else joint_min_position

    t_s = [0.0, travel_duration]
    x_m = [start_position, end_position]
    v_m = [0.0, 0.0] if is_use_velocity else None
    a_m = [0.0, 0.0] if is_use_acceleration else None

    joint.trajectory.clear()

    for index in range(len(t_s)):
        joint.trajectory.add(
            t_s=t_s[index],
            x_m=x_m[index] if x_m else None,
            v_m=v_m[index] if v_m else None,
            a_m=a_m[index] if a_m else None,
        )

    return TrajectoryFlattened(t_s, x_m, v_m, a_m)


def _map_range(value, map_from: tuple[float, float], map_to: tuple[float, float]):
    """
    Maps a value from one range to another.
    """
    original_min, original_max = map_from
    target_min, target_max = map_to

    if original_min >= original_max or target_min >= target_max:
        raise ValueError("Min cannot be greater or equal to max")

    # Linear mapping:
    return (target_max - target_min) / (original_max - original_min) * (
        value - original_min
    ) + target_min


class TrajectoryCalibrationData:
    """
    Controls calibration and data collection for one direction of joint motion.

    See `MotionData::is_calibrated()` for calibration conditions.
    """

    def __init__(
        self,
        description: str,
        battery_info: BatteryInfo,
        is_positive_direction: bool,
        is_use_velocity: bool,
        is_use_acceleration: bool,
        calibration_targets: CalibrationTargets,
    ) -> None:

        self.description = description
        self.battery_info = battery_info
        self.is_positive_direction = is_positive_direction
        self.is_use_velocity = is_use_velocity
        self.is_use_acceleration = is_use_acceleration
        self.calibration_targets = calibration_targets

        self.motion_data: list[MotionData] = []

        self.messages = []

        self.last_good_calibration: MotionData|None = None
        self.last_bad_calibration: MotionData|None = None
        self.optimal_calibration_motion_data: MotionData | None = None

    def is_calibrated(self):
        return self.optimal_calibration_motion_data is not None

    def _get_dynamic_decrease_time_by(self, motion_data: MotionData):
        """
        Linearly decreases the travel duration by a value between 0.1 and 1.5, depending on distance to the goal.
        """
        decrement_by = self.calibration_targets.travel_duration_decrement_by_max_seconds

        return np.min(
            [
                decrement_by
                - _map_range(
                    motion_data.error_percent,
                    (0, self.calibration_targets.goal_error_percentage_target),
                    (0.1, decrement_by),
                ),
                decrement_by
                - _map_range(
                    motion_data.effort_percent_max,
                    (0, self.calibration_targets.effort_percent_target),
                    (0.1, decrement_by),
                ),
            ]
        )


    @property
    def profile_name(self):
        if self.is_use_acceleration:
            return "Quintic"
        if self.is_use_velocity:
            return "Cubic"
        return "Linear"

    @property
    def direction_name(self):
        return "Positive" if self.is_positive_direction else "Negative"


    def _good_step(self, motion_data:MotionData):
        motion_data.step_calibration_result = (
            StepCalibrationResult.TARGETS_NOT_REACHED
        )

        self.last_good_calibration = motion_data

        # Add the motion_data after adding all the correct statuses and attributes.
        self.motion_data.append(motion_data)
        
        return motion_data.motion_overview(
                f"""
{self.direction_name} {joint.name} {self.profile_name} Motion Profile:
"""
            )
        

    def _bad_step(self, motion_data:MotionData):
        """
        We've landed on a bad step. This means that we've exceeded the calibration targets.
        We now want to set this as the upper bound, and bring the good step as close as possible.
        """

        is_first_time_backtracking = self.last_bad_calibration is None
        self.last_bad_calibration = motion_data

        motion_data.step_calibration_result = (
            StepCalibrationResult.BACKTRACKING_INCREASING_TIME
        )

        if is_first_time_backtracking:
            motion_data.step_calibration_result = (
                StepCalibrationResult.FIRST_OVERSHOOT
            )

        # Add the motion_data after adding all the correct statuses and attributes.
        self.motion_data.append(motion_data)

        return motion_data.motion_overview(
                f"""
{self.direction_name} {joint.name} {self.profile_name} Motion Profile: 
The  dynamic range has been exceeded. Step_calibration is backtracking to find the optimal calibration values. 
"""
            )

    def get_next_travel_duration_in_seconds(self) -> tuple[float, float, str]:
        amount = self.calibration_targets.travel_duration_start_seconds
        change_time_by = amount

        good_travel_duration = self.last_good_calibration.trajectory.travel_duration_seconds if self.last_good_calibration else None
        bad_travel_duration = self.last_bad_calibration.trajectory.travel_duration_seconds if self.last_bad_calibration else None
        STOPPED_FOR_SAFETY_MOTION_PENALTY = 0.2


        if not good_travel_duration and not bad_travel_duration:
            return amount, change_time_by, ""

        message = f"""New {self.direction_name} calibration step:"""
        
        if good_travel_duration and not bad_travel_duration and self.last_good_calibration:
            # We need to speed up motion and decrease the time step:
            change_time_by = -1 * self._get_dynamic_decrease_time_by(self.last_good_calibration)

            amount = round(good_travel_duration + change_time_by, 2)

            message +=f"""
    Decreasing the last travel time from {good_travel_duration}s to {amount}s ({change_time_by}s) for this run.
    """

        if not good_travel_duration and bad_travel_duration and self.last_bad_calibration:
            # We've already overshot without finding a good value.
            raise ValueError(f"Bad initial travel duration in Calibration Targets. Started at {bad_travel_duration}s, achieiving {self.last_bad_calibration.linear_speed_cm_per_second}m/s, and faulted. Please review the Calibration Targets: {self.calibration_targets}")

        if good_travel_duration and bad_travel_duration and self.last_bad_calibration and self.last_good_calibration:
            # We need to slow down motion and increase the time step:
            change_time_by = (good_travel_duration - bad_travel_duration) /2

            if self.last_motion_stopped_for_safety:
                change_time_by -= STOPPED_FOR_SAFETY_MOTION_PENALTY

            amount = round(good_travel_duration - change_time_by, 2)

            message +=f"""
    Increasing the last travel time from {bad_travel_duration}s to {amount}s (+{change_time_by}s) for this run.
    The last known good travel time is {good_travel_duration}s. {'NOTE: The last run motion was stopped for safety.' if {self.last_motion_stopped_for_safety} else ''}
    """

        
        return amount, change_time_by, message

    def _check_runstop(self, motion_data:MotionData):
        pimu.pull_status()
        is_runstopped = pimu.status['runstop_event']
        if is_runstopped:
            motion_data.is_motion_stopped_for_safety = True

            while is_runstopped:
                pimu.pull_status()
                is_runstopped = pimu.status['runstop_event']

                print(f"Runstopped, waiting to resume. {BatteryInfo.get_battery_info(pimu)}")

                time.sleep(3)

    def step_calibration(self, joint: PrismaticJoint):
        """
        Decreases the `current_travel_duration` until one of the `is_calibrated()` conditions is met.

        Note: calling `step_calibration()` after `is_calibrated()` is true will use the best calibration values to move the joint, but will not collect new data.
        """

        travel_duration, change_time_by, message = self.get_next_travel_duration_in_seconds()

        end_condition_1 = self.last_bad_calibration and abs(change_time_by) < 0.25 and not self.last_motion_stopped_for_safety

        if self.last_good_calibration and end_condition_1:
            # we're close enough, accept this motion_data as optimal
            self.optimal_calibration_motion_data = self.last_good_calibration
            self.optimal_calibration_motion_data.step_calibration_result = StepCalibrationResult.TARGET_REACHED

            # don't change the travel duration for the next run.
            travel_duration = self.last_good_calibration.trajectory.travel_duration_seconds
        else:
            print(message)

        # Set the motion trajectory:
        trajectory = _set_trajectory_based_on_joint_limits(
            joint=joint,
            is_positive_direction=self.is_positive_direction,
            travel_duration=travel_duration,
            is_use_velocity=self.is_use_velocity,
            is_use_acceleration=self.is_use_acceleration,
            offset_from_joint_limit_min=self.calibration_targets.offset_from_joint_limit_min,
            offset_from_joint_limit_max=self.calibration_targets.offset_from_joint_limit_max,
        )

        # Run the motion and collect motion data:
        motion_data = _run_profile_trajectory(
            joint=joint,
            trajectory=trajectory,
            calibration_targets=self.calibration_targets,
        )

        if self.is_calibrated():
            print(f"\n    The {self.direction_name} dynamic range is already calibrated, but step_calibration did the motion anyway.\n"
                )
            return False


        self._check_runstop(motion_data)

        self.last_motion_stopped_for_safety = motion_data.is_motion_stopped_for_safety

        message = ""

        if (
            not motion_data.is_exceeded_calibration_targets()
            and not motion_data.is_motion_stopped_for_safety
        ):
            message = self._good_step(motion_data)
        else:
            message = self._bad_step(motion_data)

        self.messages.append(message)

        print(message)

        return True


    def to_json(self, is_export_only_last_motion_data=True):
        return json.loads(
            json.dumps(
                {
                    "description": self.description,
                    "travel_duration_seconds": self.optimal_calibration_motion_data.trajectory.travel_duration_seconds if self.optimal_calibration_motion_data else None,
                    "travel_range_cm": self.optimal_calibration_motion_data.trajectory.trajectory_range if self.optimal_calibration_motion_data else None,
                    "linear_speed_cm_per_second": self.optimal_calibration_motion_data.linear_speed_cm_per_second if self.optimal_calibration_motion_data else None,
                    "is_positive_direction": self.is_positive_direction,
                    "is_use_velocity": self.is_use_velocity,
                    "is_use_acceleration": self.is_use_acceleration,
                    "calibration_targets": asdict(self.calibration_targets),
                    "motion_data": [
                        motion_data.to_json()
                        for motion_data in (
                            self.motion_data[-1:]
                            if is_export_only_last_motion_data
                            else self.motion_data
                        )
                    ],
                    "battery_info": self.battery_info.to_json(),
                    "last_good_calibration": (
                        self.last_good_calibration.to_json()
                        if self.last_good_calibration is not None
                        else None
                    ),
                    "last_bad_calibration": (
                        self.last_bad_calibration.to_json()
                        if self.last_bad_calibration is not None
                        else None
                    ),
                    "optimal_calibration_motion_data": (
                        self.optimal_calibration_motion_data.to_json()
                        if self.optimal_calibration_motion_data is not None
                        else None
                    ),
                    "messages": self.messages,
                }
            )
        )

    @staticmethod
    def from_json(json_data: dict):
        calibration_data = TrajectoryCalibrationData(
            description=json_data["description"],
            battery_info=BatteryInfo(**json_data["battery_info"]),
            is_positive_direction=json_data["is_positive_direction"],
            is_use_velocity=json_data["is_use_velocity"],
            is_use_acceleration=json_data["is_use_acceleration"],
            calibration_targets=json_data["calibration_targets"],
        )
        motion_data_json: list[dict] = json_data["motion_data"]
        calibration_data.motion_data = [
            MotionData.from_json(motion_data) for motion_data in motion_data_json
        ]
        calibration_data.messages = json_data["messages"]
        calibration_data.last_bad_calibration = MotionData.from_json(
            json_data["last_bad_calibration"]
        )

        calibration_data.last_good_calibration = MotionData.from_json(
            json_data["last_good_calibration"]
        )

        calibration_data.optimal_calibration_motion_data = MotionData.from_json(
            json_data["optimal_calibration_motion_data"]
        )

        return calibration_data


def _do_calibration_trajectory_mode_dynamic_limits(
    joint: PrismaticJoint,
    is_use_velocity: bool,
    is_use_acceleration: bool,
    filename_prefix: str,
    positive_calibration_targets: CalibrationTargets,
    negative_calibration_targets: CalibrationTargets,
):
    """
    Uses trajectory mode to construct paths, to dynamically calibrate dynamic limits for your robot's joint.

    NOTE: guarded contact limits will be disabled for this calibration, and this code will monitor current draw (effort) directly.

    See `calibration_trajectory_mode_dynamic_limits()` for more information
    """

    battery_info = BatteryInfo.get_battery_info(pimu)
    print(battery_info)

    positive_motion = TrajectoryCalibrationData(
        description=f"{joint.name} Positive",
        battery_info=battery_info,
        is_positive_direction=True,
        is_use_velocity=is_use_velocity,
        is_use_acceleration=is_use_acceleration,
        calibration_targets=positive_calibration_targets,
    )
    negative_motion = TrajectoryCalibrationData(
        description=f"{joint.name} Negative",
        battery_info=battery_info,
        is_positive_direction=False,
        is_use_velocity=is_use_velocity,
        is_use_acceleration=is_use_acceleration,
        calibration_targets=negative_calibration_targets,
    )

    while not positive_motion.is_calibrated() or not negative_motion.is_calibrated():

        new_motion_to_plot = positive_motion.step_calibration(joint=joint)

        if new_motion_to_plot:
            plot_motion_profiles_and_save_outputs(
                calibration_data=positive_motion,
                motion_data=positive_motion.motion_data[-1],
                filename_prefix=filename_prefix,
            )

        new_motion_to_plot = negative_motion.step_calibration(joint=joint)

        if new_motion_to_plot:
            plot_motion_profiles_and_save_outputs(
                calibration_data=negative_motion,
                motion_data=positive_motion.motion_data[-1],
                filename_prefix=filename_prefix,
            )

    # Save and print optimal motion profile data:

    optimal_positive = positive_motion.optimal_calibration_motion_data
    optimal_negative = negative_motion.optimal_calibration_motion_data
    if optimal_positive is None or optimal_negative is None:
        raise Exception("Calibration failed.")

    plot_motion_profiles_and_save_outputs(
        calibration_data=positive_motion,
        motion_data=optimal_positive,
        filename_prefix="optimal_" + filename_prefix,
    )
    plot_motion_profiles_and_save_outputs(
        calibration_data=negative_motion,
        motion_data=optimal_negative,
        filename_prefix="optimal_" + filename_prefix,
    )

    print(
        f"""
Optimal Positive {joint.name} {positive_motion.profile_name} Motion Profile: 
{optimal_positive.motion_overview()}

Optimal Negative {joint.name} {negative_motion.profile_name} Motion Profile: 
{optimal_negative.motion_overview()}
"""
    )

    results = CalibrationResults(
        **{
            "effort_pct_pos": [
                motion_data.effort_during_motion
                for motion_data in positive_motion.motion_data[-4:]
            ],
            "effort_pct_neg": [
                motion_data.effort_during_motion
                for motion_data in negative_motion.motion_data[-4:]
            ],
            "pos_out": [
                motion_data.positions_during_motion
                for motion_data in positive_motion.motion_data[-4:]
            ],
            "pos_in": [
                motion_data.positions_during_motion
                for motion_data in negative_motion.motion_data[-4:]
            ],
            "max_effort_pct_pos": positive_motion.motion_data[-1].effort_percent_max,
            "min_effort_pct_neg": negative_motion.motion_data[-1].effort_percent_min,
        }
    )

    return results


def run_calibration_trajectory(joint: PrismaticJoint, label: str):
    """
    Uses trajectory mode to construct paths, to dynamically calibrate dynamic limits for your robot's joint.

    NOTE: guarded contact limits will be disabled for this calibration, and this code will monitor current draw (effort) directly.

    Trajectory mode uses three profiles: linear, cubic and quintic.
    - The Linear profile provides position steps only.
    - The Cubic profile provides postion and velocity steps.
    - The Quintic profile provides position, velocity and acceleration steps.

    *Linear calibration*:
    A trajectory with the minimum and maximum limit positions of the joint will be used.
    The arrival time will be calibrated to find a profile that utilizes about 80% effort.

    *Cubic calibration*
    A trajectory with the minimum and maximum limit positions of the joint will be used.
    Velocity steps will be set to 0 m/s at either extremes.
    The arrival time will be calibrated to find a profile that utilizes about 80% effort.

    *Quintic calibration*
    A trajectory with the minimum and maximum limit positions of the joint will be used.
    Velocity steps will be set to 0 m/s at either extremes.
    Acceleration steps will be set to 0 m/s^2 at either extremes.
    The arrival time will be calibrated to find a profile that utilizes about 80% effort.
    """

    filename_prefix = f"{label}_"  # time in ms

    # Linear:
    tictoc_timer("Linear Calibration")
    results_linear = _do_calibration_trajectory_mode_dynamic_limits(
        joint=joint,
        is_use_velocity=False,
        is_use_acceleration=False,
        filename_prefix=filename_prefix,
        positive_calibration_targets=CalibrationTargets.linear_default(),
        negative_calibration_targets=CalibrationTargets.linear_default(),
    )
    tictoc_timer("Linear Calibration")

    # Cubic:
    tictoc_timer("Cubic Calibration")
    results_cubic = _do_calibration_trajectory_mode_dynamic_limits(
        joint=joint,
        is_use_velocity=True,
        is_use_acceleration=False,
        filename_prefix=filename_prefix,
        positive_calibration_targets=CalibrationTargets.cubic_default(),
        negative_calibration_targets=CalibrationTargets.cubic_default(),
    )
    tictoc_timer("Cubic Calibration")

    # Quintic:
    tictoc_timer("Quintic Calibration")
    results_quintic = _do_calibration_trajectory_mode_dynamic_limits(
        joint=joint,
        is_use_velocity=True,
        is_use_acceleration=True,
        filename_prefix=filename_prefix,
        positive_calibration_targets=CalibrationTargets.quintic_default(),
        negative_calibration_targets=CalibrationTargets.quintic_default(),
    )
    tictoc_timer("Quintic Calibration")

    return [results_linear, results_cubic, results_quintic]


tictoc_timer_tracker = {}


def tictoc_timer(tag: str):
    """
    Call it the first time to start a timer. Call it again to print out the time difference.
    """
    global tictoc_timer_tracker
    if tag in tictoc_timer_tracker:

        time_taken_seconds = time.time() - tictoc_timer_tracker[tag]

        minutes = int(time_taken_seconds // 60)
        seconds = round(time_taken_seconds % 60, 2)

        print(f"{tag}: Time taken: {minutes}:{seconds}")

        del tictoc_timer_tracker[tag]

        return (minutes, seconds)

    print("Started Timer", tag)
    tictoc_timer_tracker[tag] = time.time()

def _run_calibration():
    global trajectory_folder_to_save_plots

    trajectory_folder_to_save_plots = get_stretch_directory(
        f"calibration_trajectory_dynamic_limits/{int(time.time())}"
    )

    os.system("mkdir -p " + trajectory_folder_to_save_plots)

    print(f"Writing to {trajectory_folder_to_save_plots}")

    tictoc_timer("Calibration Trajectory")

    robot_name = __import__("platform").node()  # get computer name
    label = f"{robot_name}_{round(time.time()*1000)}"

    run_calibration_trajectory(joint, label=label)

    tictoc_timer("Calibration Trajectory")

def _idle_move_joint(target_voltage:float, joint:PrismaticJoint):
    """
    Wait for battery to reach a target
    """
    joint.motor.disable_sync_mode()
    joint.push_command()

    battery_voltage = BatteryInfo.get_battery_info(pimu).battery_voltage 

    to_position = 0.2
    while target_voltage < battery_voltage:
        battery_voltage = BatteryInfo.get_battery_info(pimu).battery_voltage 
        print(f"Idling while waiting for battery to reach {target_voltage}. Currently: {battery_voltage}")
        
        joint.move_to(to_position)
        to_position = 0.6 if to_position == 0.2 else 0.2

        joint.push_command()
        joint.motor.wait_until_at_setpoint()

        time.sleep(5)

    return battery_voltage

if __name__ == "__main__":
    print_stretch_re_use()

    parser = argparse.ArgumentParser(
        description="Calibrate the default guarded contacts for a joint."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--lift", help="Calibrate the lift joint", action="store_true")
    group.add_argument("--arm", help="Calibrate the arm joint", action="store_true")
    parser.add_argument(
        "--ncycle", type=int, help="Number of sweeps to run [4]", default=4
    )
    parser.add_argument("--skip_homing", help="Skip joint homing", action="store_true")
    parser.add_argument("--run_continously_until_battery_low", help="Runs calibration continuously until the battery is low.", action="store_true")
    args = parser.parse_args()

    if not args.skip_homing:
        click.secho(
            "The Lift, Arm and Wrist yaw will need to be first homed. Ensure workspace is collision free.",
            fg="yellow",
        )
        if not click.confirm("Proceed?"):
            exit(0)

        subprocess.call(
            "stretch_lift_home.py"
        )  # Home the lift first to avoid the arm slamming into the ground at lift=0
        subprocess.call("stretch_arm_home.py")
        subprocess.call("stretch_wrist_yaw_home.py")

    joint = Lift()

    if args.arm:
        joint = Arm()

    check_deprecated_contact_model_prismatic_joint(
        joint, "REx_calibrate_guarded_contacts.py", None, None, None, None
    )

    if not joint.startup(threaded=False):
        exit(1)

    joint.pull_status()
    if not joint.motor.status["pos_calibrated"]:
        print("Joint not calibrated. Exiting.")
        exit(1)

    pimu = Pimu()
    if not pimu.startup(threaded=False):
        print("Could not start the PIMU")
        exit(1)

    pimu.pull_status()

    if (
        (
            joint.name in joint.user_params
            and "contact_models" in joint.user_params[joint.name]
        )
        and ("effort_pct" in joint.user_params[joint.name]["contact_models"])
        and (
            "contact_thresh_default"
            in joint.user_params[joint.name]["contact_models"]["effort_pct"]
        )
    ):
        click.secho("------------------------", fg="yellow")
        click.secho(
            "NOTE: This tool updates contact_thresh_default for %s in stretch_configuration_params.yaml"
            % joint.name.upper(),
            fg="yellow",
        )
        click.secho(
            "NOTE: Your stretch_user_params.yaml overrides contact_thresh_default for %s"
            % joint.name.upper(),
            fg="yellow",
        )
        click.secho(
            "NOTE: As such, the updated calibration will not change the contact behavior unless you remove the user params.",
            fg="yellow",
        )
    click.secho("------------------------", fg="yellow")
    click.secho(
        """
Joint %s will go through its full range-of-motion.
1. Ensure workspace is collision free
2. Dynamic limits will be significantly increased - effectively disabled - for the duration of this test, be careful!
3. The lift or joints may suddenly accelerate and/or freefall. Safety measures are in place to brake the motors, however, still be careful!
"""
        % joint.name.capitalize(),
        fg="yellow",
    )
    if click.confirm("Proceed?"):

        _run_calibration()

        if args.run_continously_until_battery_low:
            current_voltage = BatteryInfo.get_battery_info(pimu).battery_voltage 
            targets = np.arange(11.0, current_voltage, 0.5)[::-1]

            print(f"Running continiously until battery low. Step targets: {targets}. Current voltage: {current_voltage}")

            for target_voltage in targets:
                current_voltage = _idle_move_joint(target_voltage=target_voltage, joint=joint)

                if current_voltage < targets[-1]:
                    print(f"Battery voltage is below the minimum, aborting the {target_voltage}V run.")
                    exit()

                print("Target battery voltage reached, starting calibration.")
                
                _run_calibration()

        


