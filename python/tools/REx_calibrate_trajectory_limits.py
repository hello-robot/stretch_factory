#!/usr/bin/python3
from dataclasses import asdict, dataclass, field
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
from stretch_body.base import Base
from stretch_body.prismatic_joint import PrismaticJoint

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

import logging

# Configure logging to output to the console
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class MotionProfileTypes(IntEnum):
    linear = 0
    cubic = 1
    quintic = 2


class JointTypes(IntEnum):
    arm = 0
    lift = 1
    base = 2

    def get_joint_instance(self):
        if self == JointTypes.arm:
            return Arm()
        if self == JointTypes.lift:
            return Lift()
        if self == JointTypes.base:
            return Base()

        raise NotImplementedError(f"{self} joint type is not supported.")

    @staticmethod
    def available_joints(run_mode: "_RunMode"):
        if run_mode != _RunMode.trajectory_effort_mode:
            return JointTypes

        # If we're running trajectory_effort_mode, return all the joints except base
        return [j for j in JointTypes if (j != JointTypes.base)]


class StepCalibrationResult(IntEnum):
    TARGETS_NOT_REACHED = 0
    FIRST_OVERSHOOT = 1  # Capturing this may help debug bad overshooting behavior
    BACKTRACKING_DECREASING_TIME = 2
    BACKTRACKING_INCREASING_TIME = 3
    TARGET_REACHED = 4
    TARGET_REACHED_JUST_DOING_MOTION = 5


@dataclass
class BatteryInfo:
    battery_voltage: float
    battery_percentage: float

    def __repr__(self) -> str:
        return f"Battery Level: {self.battery_voltage}V ({self.battery_percentage}%)"

    def to_json(self) -> dict:
        return json.loads(json.dumps(asdict(self)))

    @staticmethod
    def get_battery_info(
        pimu: "Pimu", max_battery_volage: float = 14.5
    ) -> "BatteryInfo":

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
    Calibration conditions, see `MotionData::is_exceeded_calibration_targets()` for more info
    """

    effort_percent_target: float  # We want to reach this target and stop
    goal_error_absolute_target_cm: float  # cm deviation from the trajectory
    goal_error_percentage_target: float  # % deviation from the trajectory goal

    travel_duration_start_seconds: float  # seconds, start slow
    travel_duration_decrement_by_max_seconds: (
        float  # seconds, maximum we can decrease duration by.
    )
    end_condition_time_step: float  # If the calibration step would decrease the time by this amount, end calibration

    offset_from_joint_limit_min: float
    offset_from_joint_limit_max: float

    @staticmethod
    def _shared_defaults(
        joint: "PrismaticJoint|Base",
        travel_duration_start_seconds: float,
        travel_duration_decrement_by_max_seconds: float,
    ) -> "CalibrationTargets":

        if isinstance(joint, Lift):
            return CalibrationTargets(
                effort_percent_target=80,
                goal_error_absolute_target_cm=1.2,
                goal_error_percentage_target=10.0,
                offset_from_joint_limit_min=0.2,
                offset_from_joint_limit_max=0.2,
                travel_duration_start_seconds=travel_duration_start_seconds,
                travel_duration_decrement_by_max_seconds=travel_duration_decrement_by_max_seconds,
                end_condition_time_step=0.3,
            )

        if isinstance(joint, Arm):
            return CalibrationTargets(
                effort_percent_target=80,
                goal_error_absolute_target_cm=1.2,
                goal_error_percentage_target=10.0,
                offset_from_joint_limit_min=0.05,
                offset_from_joint_limit_max=0.05,
                travel_duration_start_seconds=travel_duration_start_seconds,
                travel_duration_decrement_by_max_seconds=travel_duration_decrement_by_max_seconds,
                end_condition_time_step=0.3,
            )

        if isinstance(joint, Base):
            return CalibrationTargets(
                effort_percent_target=80,
                goal_error_absolute_target_cm=0.5,
                goal_error_percentage_target=5.0,
                offset_from_joint_limit_min=1.0,
                offset_from_joint_limit_max=-1.0,
                travel_duration_start_seconds=travel_duration_start_seconds,
                travel_duration_decrement_by_max_seconds=travel_duration_decrement_by_max_seconds,
                end_condition_time_step=0.3,
            )

        raise NotImplementedError(
            f"Joint {joint.name} is not supported for trajectory calibration."
        )

    @staticmethod
    def linear_default(joint: "PrismaticJoint|Base") -> "CalibrationTargets":

        if isinstance(joint, Lift):
            return CalibrationTargets._shared_defaults(
                joint=joint,
                travel_duration_start_seconds=9.0,
                travel_duration_decrement_by_max_seconds=3.5,
            )

        if isinstance(joint, Arm):
            return CalibrationTargets._shared_defaults(
                joint=joint,
                travel_duration_start_seconds=9.0,
                travel_duration_decrement_by_max_seconds=3.5,
            )

        if isinstance(joint, Base):
            return CalibrationTargets._shared_defaults(
                joint=joint,
                travel_duration_start_seconds=9.0,
                travel_duration_decrement_by_max_seconds=3.0,
            )

        raise NotImplementedError(
            f"Joint {joint.name} is not supported for trajectory calibration."
        )

    @staticmethod
    def cubic_default(joint: "PrismaticJoint|Base") -> "CalibrationTargets":
        if isinstance(joint, Lift):
            return CalibrationTargets._shared_defaults(
                joint=joint,
                travel_duration_start_seconds=10.0,
                travel_duration_decrement_by_max_seconds=3.0,
            )

        if isinstance(joint, Arm):
            return CalibrationTargets._shared_defaults(
                joint=joint,
                travel_duration_start_seconds=10.0,
                travel_duration_decrement_by_max_seconds=3.0,
            )

        if isinstance(joint, Base):
            return CalibrationTargets._shared_defaults(
                joint=joint,
                travel_duration_start_seconds=16.0,
                travel_duration_decrement_by_max_seconds=3.0,
            )

        raise NotImplementedError(
            f"Joint {joint.name} is not supported for trajectory calibration."
        )

    @staticmethod
    def quintic_default(joint: "PrismaticJoint|Base") -> "CalibrationTargets":

        if isinstance(joint, Lift):
            return CalibrationTargets._shared_defaults(
                joint=joint,
                travel_duration_start_seconds=14.0,
                travel_duration_decrement_by_max_seconds=3.0,
            )
        if isinstance(joint, Arm):
            return CalibrationTargets._shared_defaults(
                joint=joint,
                travel_duration_start_seconds=14.0,
                travel_duration_decrement_by_max_seconds=3.0,
            )

        if isinstance(joint, Base):
            return CalibrationTargets._shared_defaults(
                joint=joint,
                travel_duration_start_seconds=21.0,
                travel_duration_decrement_by_max_seconds=3.0,
            )

        raise NotImplementedError(
            f"Joint {joint.name} is not supported for trajectory calibration."
        )


@dataclass
class MotionData:
    """
    Keeps track of timestamps, joint positions, and motor efforts during motion.

    Provides a `collect_data()` method to sample data.
    """

    trajectory: "TrajectoryFlattened"
    calibration_targets: "CalibrationTargets"
    timestamps_during_motion: list[float] = field(default_factory=list)
    positions_during_motion: list[float] = field(default_factory=list)
    velocities_during_motion: list[float] = field(default_factory=list)
    effort_during_motion: list[float] = field(default_factory=list)
    current_during_motion: list[float] = field(default_factory=list)
    step_calibration_result: StepCalibrationResult | None = None

    is_motion_stopped_for_safety: bool = False

    # For DiffDrive
    positions_y_during_motion: list[float] = field(default_factory=list)
    positions_theta_during_motion: list[float] = field(default_factory=list)
    velocities_y_during_motion: list[float] = field(default_factory=list)
    velocities_theta_during_motion: list[float] = field(default_factory=list)
    effort_2_during_motion: list[float] = field(default_factory=list)
    current_2_during_motion: list[float] = field(default_factory=list)

    def motion_overview(self, joint: "PrismaticJoint|Base", prefix: str = "") -> str:
        warnings = ""
        if not np.isclose(
            self.goal_position_cm,
            self.actual_position_cm,
            atol=self.calibration_targets.goal_error_absolute_target_cm,
        ):
            warnings += f"WARNING: the {joint.name} did not reach the goal.\n    "

        if self.is_motion_stopped_for_safety:
            warnings += f"WARNING: the {joint.name}'s motion was stopped for safety before completing the trajectory.\n    "

        return f"""{prefix}
    Moved {self.travel_range_cm}cm in {self.trajectory.travel_duration_seconds} seconds ({self.linear_speed_cm_per_second})cm/s. 
    Max Velocity {self.max_velocity_during_motion}. Max Acceleration: {self.max_acceletation_during_motion}
    Average effort: {self.effort_percent_average_last_10_readings}%, Abs Max Effort: {self.effort_percent_max_absolute}, Max effort: {self.effort_percent_max}% , Min effort: {self.effort_percent_min}%
    Goal Position: {self.goal_position_cm}cm. Sampled Position: {self.actual_position_cm}cm. Error: {self.error_percent}% ({self.error_absolute_cm}cm)
    Target effort reached? {self.is_exceeds_effort_target()} 
    Target absolute goal position error reached? {self.is_exceeds_absolute_goal_error_target()}
    Target percentage goal position error reached? {self.is_exceeds_percent_goal_error_target()}
    {warnings}
"""

    @property
    def last_max_effort_during_motion(self) -> float:
        effort = np.max(np.abs(self.effort_during_motion[-1]))
        return float(effort)

    @property
    def timestamps_normalized(self):

        return np.subtract(
            self.timestamps_during_motion, np.min(self.timestamps_during_motion)
        )

    @property
    def positions_cm(self):
        return np.round(np.multiply(self.positions_during_motion, 100), 2)

    @property
    def accelerations(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Returns a tuple of accelerations (m/s^2) and the timestamps corresponding to those values.
        """
        timestamps_normalized = self.timestamps_normalized

        accelerations = np.diff(self.velocities_during_motion) / np.diff(
            timestamps_normalized
        )

        # To match the lengths for plotting, average timestamps between each pair of points:
        acceleration_times = (
            np.add(timestamps_normalized[:-1], timestamps_normalized[1:])
        ) / 2

        return (accelerations, acceleration_times)
    
    @property
    def max_velocity_during_motion(self) -> float:
        if not self.velocities_during_motion:
            return 0
        return float(np.max(np.abs(self.velocities_during_motion)))
    
    @property
    def max_acceletation_during_motion(self) -> float:
        accelerations = self.accelerations[0]
        if accelerations.size == 0: return 0
        return float(np.max(np.abs(accelerations)))

    def is_exceeds_effort_target(self) -> bool:
        return (
            self.effort_percent_max_absolute
            >= self.calibration_targets.effort_percent_target
        )

    def is_exceeds_absolute_goal_error_target(self) -> bool:
        return (
            self.error_absolute_cm
            >= self.calibration_targets.goal_error_absolute_target_cm
        )

    def is_exceeds_percent_goal_error_target(self) -> bool:
        return (
            self.error_percent >= self.calibration_targets.goal_error_percentage_target
        )

    def is_exceeded_calibration_targets(self) -> bool:
        """
        Trajectory joint calibration is considered complete when ONE of these conditions are satisfied:
        1. Joint effort > EFFORT_TARGET (80%).
        2. Position % error from the trajectory goal is > 10%.
        3. Absolute Position error from the trajectory goal is > MAX_ABSOLUTE_GOAL_ERROR (1.2cm).
        """
        return (
            self.is_exceeds_effort_target()
            or self.is_exceeds_absolute_goal_error_target()
            or self.is_exceeds_percent_goal_error_target()
        )

    def current_linear_speed_meters_per_second(self, is_round: bool = True) -> float:
        speed = float(
            self.trajectory.trajectory_range / self.trajectory.travel_duration_seconds
        )
        return round(speed, 2) if is_round else speed

    def _to_cm(self, value: float) -> float:
        return round(value * 100, 2)

    @property
    def goal_position_cm(self) -> float:
        return self._to_cm(self.trajectory.positions[-1])

    @property
    def actual_position_cm(self) -> float:
        return self.positions_cm[-1]

    @property
    def error_absolute_cm(self) -> float:
        return round(abs(self.goal_position_cm - self.actual_position_cm), 2)

    @property
    def error_percent(self) -> float:
        return round(self.error_absolute_cm / self.goal_position_cm * 100, 2)

    @property
    def effort_percent_average_last_10_readings(self) -> float:
        return round(float(np.average(np.abs(self.effort_during_motion[-10:]))), 2)

    @property
    def effort_percent_max_absolute(self) -> float:
        # Take the max of both negative and positive efforts:
        return float(
            np.max((np.max(self.effort_percent_max), np.abs(self.effort_percent_min)))
        )

    @property
    def effort_percent_max(self) -> float:
        return round(float(np.max(self.effort_during_motion)), 2)

    @property
    def effort_percent_min(self) -> float:
        return round(float(np.min(self.effort_during_motion)), 2)

    @property
    def linear_speed_cm_per_second(self) -> float:
        return self._to_cm(self.current_linear_speed_meters_per_second(is_round=False))

    @property
    def travel_range_cm(self) -> float:
        return self._to_cm(self.trajectory.trajectory_range)

    def to_json(self) -> dict:
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
    def from_json(json_data: dict) -> "MotionData":
        return MotionData(
            trajectory=TrajectoryFlattened(**json_data["trajectory"]),
            calibration_targets=CalibrationTargets(**json_data["calibration_targets"]),
            timestamps_during_motion=json_data["timestamps_during_motion"],
            positions_during_motion=json_data["positions_during_motion"],
            velocities_during_motion=json_data["velocities_during_motion"],
            effort_during_motion=json_data["effort_during_motion"],
            current_during_motion=json_data["current_during_motion"],
            step_calibration_result=(
                StepCalibrationResult(json_data["step_calibration_result"])
                if json_data["step_calibration_result"]
                else None
            ),
        )


@dataclass
class TrajectoryFlattened:
    """
    Definition of a waypoint trajectory - flattened so that indecies correspond to the waypoint number. e.g. index 0 is the first waypoint.
    """

    timestamps: list[float] = field(default_factory=list)
    positions: list[float] = field(default_factory=list)
    velocities: list[float] | None = None
    accelerations: list[float] | None = None

    # For diff drive:
    positions_y: list[float] = field(default_factory=list)
    thetas: list[float] = field(default_factory=list)
    velocities_translational: list[float] | None = None
    accelerations_translational: list[float] | None = None

    def to_json(self) -> dict:
        return json.loads(json.dumps(asdict(self)))

    @property
    def travel_duration_seconds(self) -> float:
        return abs(self.timestamps[-1] - self.timestamps[0])

    @property
    def x_range(self) -> float:
        return float(abs(np.ptp(self.positions)))

    @property
    def y_range(self) -> float:
        return float(abs(np.ptp(self.positions_y))) if self.positions_y else 0

    @property
    def trajectory_range(self) -> float:
        return float(np.linalg.norm(np.array((self.x_range, self.y_range))))


@dataclass
class TrajectoryCalibrationData:
    """
    Controls calibration and data collection for one direction of joint motion.

    See `MotionData::is_exceeded_calibration_targets()` for calibration conditions.
    """

    description: str
    battery_info: BatteryInfo
    motion_type: MotionProfileTypes
    is_positive_direction: bool
    is_use_velocity: bool
    is_use_acceleration: bool
    calibration_targets: CalibrationTargets

    motion_data: list[MotionData] = field(default_factory=list)

    messages: list[str] = field(default_factory=list)

    last_good_calibration: MotionData | None = None
    last_bad_calibration: MotionData | None = None
    optimal_calibration_motion_data: MotionData | None = None

    last_motion_stopped_for_safety = False

    def is_calibrated(self) -> bool:
        return self.optimal_calibration_motion_data is not None

    def get_optimal_calibration_motion_data(self):
        if self.optimal_calibration_motion_data is None:
            raise Exception(
                "Optimal calibration data is not available. Did calibration complete?"
            )
        return self.optimal_calibration_motion_data

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

    def to_json(self, is_export_only_last_motion_data=True) -> dict:
        return json.loads(
            json.dumps(
                {
                    "description": self.description,
                    "motion_type": self.motion_type,
                    "travel_duration_seconds": (
                        self.optimal_calibration_motion_data.trajectory.travel_duration_seconds
                        if self.optimal_calibration_motion_data
                        else None
                    ),
                    "travel_range_cm": (
                        self.optimal_calibration_motion_data.trajectory.trajectory_range
                        if self.optimal_calibration_motion_data
                        else None
                    ),
                    "linear_speed_cm_per_second": (
                        self.optimal_calibration_motion_data.linear_speed_cm_per_second
                        if self.optimal_calibration_motion_data
                        else None
                    ),
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
    def from_json(json_data: dict) -> "TrajectoryCalibrationData":
        calibration_data = TrajectoryCalibrationData(
            description=json_data["description"],
            battery_info=BatteryInfo(**json_data["battery_info"]),
            is_positive_direction=json_data["is_positive_direction"],
            is_use_velocity=json_data["is_use_velocity"],
            is_use_acceleration=json_data["is_use_acceleration"],
            calibration_targets=json_data["calibration_targets"],
            motion_type=MotionProfileTypes(json_data["motion_type"]),
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


def _collect_data_prismatic(motion_data: MotionData, joint: "PrismaticJoint"):
    motion_data.timestamps_during_motion.append(time.time())
    motion_data.positions_during_motion.append(joint.status["pos"])
    motion_data.velocities_during_motion.append(joint.status["vel"])
    motion_data.effort_during_motion.append(joint.motor.status["effort_pct"])
    motion_data.current_during_motion.append(joint.motor.status["current"])


def _collect_data_base(
    motion_data: MotionData,
    joint: "Base",
    starting_position: tuple[float, float, float],
):
    motion_data.timestamps_during_motion.append(time.time())

    x = (
        joint.status["x"] - starting_position[0]
    )  # Convert relative position to absolute
    y = (
        joint.status["y"] - starting_position[1]
    )  # Convert relative position to absolute
    theta = (
        joint.status["theta"] - starting_position[2]
    )  # Convert relative position to absolute
    x_vel = joint.status["x_vel"]
    y_vel = joint.status["y_vel"]
    theta_vel = joint.status["theta_vel"]

    motion_data.positions_during_motion.append(x)
    motion_data.positions_y_during_motion.append(y)
    motion_data.positions_theta_during_motion.append(theta)

    motion_data.velocities_during_motion.append(x_vel)
    motion_data.velocities_y_during_motion.append(y_vel)
    motion_data.velocities_theta_during_motion.append(theta_vel)

    current = joint.status["left_wheel"]["current"]
    current_right_wheel = joint.status["right_wheel"]["current"]

    # TODO: use effort for both wheels.
    effort = joint.status["left_wheel"]["effort_pct"]
    effort_2 = joint.status["right_wheel"]["effort_pct"]

    motion_data.effort_during_motion.append(effort)
    motion_data.effort_2_during_motion.append(effort_2)
    motion_data.current_during_motion.append(current)
    motion_data.current_2_during_motion.append(current_right_wheel)


def _collect_data(
    motion_data: MotionData,
    joint: "Base|PrismaticJoint",
    starting_position: tuple[float, float, float],
):
    # is this "reflection" too slow?
    if not isinstance(joint, Base):
        _collect_data_prismatic(motion_data=motion_data, joint=joint)
    else:
        _collect_data_base(
            motion_data=motion_data, joint=joint, starting_position=starting_position
        )


def _plot_motion_profiles_and_save_outputs(
    calibration_data: "TrajectoryCalibrationData",
    motion_data: "MotionData",
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
    plt.tight_layout(rect=(0.0, 0.03, 1.0, 0.95))
    if show_plot:
        matplotlib.use(
            "TKAgg"
        )  # Makes headless/remote connection plotting possible with an Xvfb display.

        plt.show(block=False)

    # Save data
    title_snakecase = f"{filename_prefix}{calibration_data.description}_{calibration_data.profile_name}_{motion_data.linear_speed_cm_per_second}cm/s"
    title_snakecase = title_snakecase.replace(" ", "_").replace("/", "_per_").lower()

    if motion_data.is_motion_stopped_for_safety:
        title_snakecase += "_stopped_for_safety"

    if motion_data.step_calibration_result == StepCalibrationResult.FIRST_OVERSHOOT:
        title_snakecase += "_first_overshoot"

    global trajectory_folder_to_save_plots
    if write_to_json:
        filename = f"{trajectory_folder_to_save_plots}/{title_snakecase}.json"
        with open(filename, "w") as json_file:
            json.dump(calibration_data.to_json(), json_file, indent=4)

    plt.savefig(f"{trajectory_folder_to_save_plots}/{title_snakecase}.png")


def run_profile_trajectory(
    joint: "PrismaticJoint|Base",
    trajectory: TrajectoryFlattened,
    calibration_targets: CalibrationTargets,
    disable_guarded_mode: bool = True,
    disable_dynamic_limits: bool = True,
) -> MotionData:
    """
    Follows a trajectory and captures position and effort data.

    This monitors joint effort and calls `joint.motor.enable_safety()` if the effort exceeds a threshold.
    """
    motion_data = MotionData(
        trajectory=trajectory, calibration_targets=calibration_targets
    )

    if isinstance(joint, Base):
        _set_trajectory_diff_drive(joint=joint, flattened_trajectory=trajectory)
    else:
        _set_trajectory(joint=joint, flattened_trajectory=trajectory)

    if len(joint.trajectory.waypoints) == 0:
        raise Exception(
            "No waypoints. Did you call _set_trajectory_based_on_joint_limits()?"
        )

    _disable_sync_mode(joint)  # this is important for trajectory mode to move joints.

    if disable_guarded_mode:
        _disable_guarded_mode(joint)

    if disable_dynamic_limits:
        if not isinstance(joint, Base):
            # We're disabling the limits for dynamic checks.
            joint.params["motion"]["trajectory_max"]["vel_m"] = 0.5
            joint.params["motion"]["trajectory_max"]["accel_m"] = 0.5
        else:
            joint.params["motion"]["trajectory_max"]["vel_r"] = 200
            joint.params["motion"]["trajectory_max"]["accel_r"] = 200

        try: del joint.params["motion"]["trajectory_max"]["linear"]
        except: ...
        try: del joint.params["motion"]["trajectory_max"]["cubic"]
        except: ...
        try: del joint.params["motion"]["trajectory_max"]["quintic"]
        except: ...

    joint.pull_status()

    time.sleep(1)  # let things settle

    if not isinstance(joint, Base):
        starting_position = joint.status["pos"]
    else:
        starting_position = (
            joint.status["x"],
            joint.status["y"],
            joint.status["theta"],
        )

    assert _follow_trajectory(joint), "Setting trajectory failed."

    time.sleep(0.25)
    joint.pull_status()
    joint.update_trajectory()
    joint.pull_status()
    SAMPLING_RATE_HZ = 10

    assert joint.is_trajectory_active(), "Trajectory is not active, when it should be."

    while joint.is_trajectory_active():
        time.sleep(1 / SAMPLING_RATE_HZ)  # Sample at 1/SAMPLING_RATE seconds

        joint.pull_status()
        joint.update_trajectory()

        _collect_data(
            motion_data=motion_data, joint=joint, starting_position=starting_position
        )

        if (
            abs(motion_data.last_max_effort_during_motion)
            > motion_data.calibration_targets.effort_percent_target
        ):
            # Effort too high!
            print(f"\n    WARNING: Effort exceeded, telling {joint.name} to stop!\n")
            _enable_safety(joint)

            motion_data.is_motion_stopped_for_safety = True

            break

    return motion_data


def _get_trajectory_based_on_joint_limits(
    joint: "PrismaticJoint",
    is_positive_direction: bool,
    travel_duration: float,
    is_use_velocity: bool,
    is_use_acceleration: bool,
    offset_from_joint_limit_min: float,
    offset_from_joint_limit_max: float,
) -> "TrajectoryFlattened":
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

    return TrajectoryFlattened(t_s, x_m, v_m, a_m)


def _get_trajectory_diff_drive(
    is_positive_direction: bool,
    travel_duration: float,
    is_use_velocity: bool,
    is_use_acceleration: bool,
    offset_from_joint_limit_min: float,
    offset_from_joint_limit_max: float,
) -> "TrajectoryFlattened":
    """
    Sets the starting and ending positions to the range limits of the joint.

    If `is_use_velocity` is true, the velocity steps will be set to 0 m/s at either extremes.
    If `is_use_acceleration` is true, the acceleration steps will be set to 0 m/s^2 at either extremes.

    returns `joint_range`
    """

    t_s = [0.0, travel_duration]
    x = [
        0.0,
        (
            offset_from_joint_limit_min
            if is_positive_direction
            else offset_from_joint_limit_max
        ),
    ]
    y = [0.0, 0.0]
    theta = [0.0, 0.0]
    translational_vel = [0.0, 0.0] if is_use_velocity else None
    rotational_vel = translational_vel
    translational_accel = [0.0, 0.0] if is_use_acceleration else None
    rotational_accel = translational_accel

    return TrajectoryFlattened(
        timestamps=t_s,
        positions=x,
        positions_y=y,
        thetas=theta,
        velocities=rotational_vel,
        velocities_translational=translational_vel,
        accelerations=rotational_accel,
        accelerations_translational=translational_accel,
    )


def _set_trajectory(
    joint: "PrismaticJoint", flattened_trajectory: "TrajectoryFlattened"
):
    joint.trajectory.clear()

    for index in range(len(flattened_trajectory.timestamps)):
        joint.trajectory.add(
            t_s=flattened_trajectory.timestamps[index],
            x_m=flattened_trajectory.positions[index],
            v_m=(
                flattened_trajectory.velocities[index]
                if flattened_trajectory.velocities
                else None
            ),
            a_m=(
                flattened_trajectory.accelerations[index]
                if flattened_trajectory.accelerations
                else None
            ),
        )


def _set_trajectory_diff_drive(
    joint: "Base", flattened_trajectory: "TrajectoryFlattened"
):

    joint.trajectory.clear()

    for index in range(len(flattened_trajectory.timestamps)):
        joint.trajectory.add(
            time=flattened_trajectory.timestamps[index],
            x=flattened_trajectory.positions[index],
            y=flattened_trajectory.positions_y[index],
            theta=flattened_trajectory.thetas[index],
            translational_vel=(
                flattened_trajectory.velocities_translational[index]
                if flattened_trajectory.velocities_translational
                else None
            ),
            rotational_vel=(
                flattened_trajectory.velocities[index]
                if flattened_trajectory.velocities
                else None
            ),
            translational_accel=(
                flattened_trajectory.accelerations_translational[index]
                if flattened_trajectory.accelerations_translational
                else None
            ),
            rotational_accel=(
                flattened_trajectory.accelerations[index]
                if flattened_trajectory.accelerations
                else None
            ),
        )


def _map_range(
    value, map_from: tuple[float, float], map_to: tuple[float, float]
) -> float:
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


def _get_dynamic_decrease_time_by(
    calibration_data: TrajectoryCalibrationData,
    motion_data: MotionData,
    is_use_effort_for_dynamic_decrease: bool,
) -> float:
    """
    Linearly decreases the travel duration by a value between 0.1 and 1.5, depending on distance to the goal.
    """
    decrement_by = (
        calibration_data.calibration_targets.travel_duration_decrement_by_max_seconds
    )

    decrement_error_percent = decrement_by - _map_range(
        motion_data.error_percent,
        (0, calibration_data.calibration_targets.goal_error_percentage_target),
        (0.1, decrement_by),
    )

    if not is_use_effort_for_dynamic_decrease:
        return decrement_error_percent

    decrement_effort = decrement_by - _map_range(
        motion_data.effort_percent_max,
        (0, calibration_data.calibration_targets.effort_percent_target),
        (0.1, decrement_by),
    )

    return np.min([decrement_error_percent, decrement_effort])


def _good_step(
    calibration_data: TrajectoryCalibrationData,
    motion_data: MotionData,
    joint: "PrismaticJoint|Base",
) -> str:
    """
    We've landed on a good step. This means we will decrease the travel duration (aka increase travel speed) to push dynamic limits further.
    """
    motion_data.step_calibration_result = StepCalibrationResult.TARGETS_NOT_REACHED

    calibration_data.last_good_calibration = motion_data

    # Add the motion_data after adding all the correct statuses and attributes.
    calibration_data.motion_data.append(motion_data)

    return motion_data.motion_overview(
        joint=joint,
        prefix=f"""
{calibration_data.direction_name} {joint.name} {calibration_data.profile_name} Motion Profile:
""",
    )


def _bad_step(
    calibration_data: TrajectoryCalibrationData,
    motion_data: MotionData,
    joint: "PrismaticJoint|Base",
) -> str:
    """
    We've landed on a bad step. This means that we've exceeded the calibration targets.
    We now want to set this as the upper bound, and bring the good step as close as possible.
    """

    is_first_time_backtracking = calibration_data.last_bad_calibration is None
    calibration_data.last_bad_calibration = motion_data

    motion_data.step_calibration_result = (
        StepCalibrationResult.BACKTRACKING_INCREASING_TIME
    )

    if is_first_time_backtracking:
        motion_data.step_calibration_result = StepCalibrationResult.FIRST_OVERSHOOT

    # Add the motion_data after adding all the correct statuses and attributes.
    calibration_data.motion_data.append(motion_data)

    backtracking_message = ""
    if run_mode == _RunMode.dynamic_limit_mode:
        backtracking_message = (
            "Step_calibration will backtrack to find the optimal calibration values."
        )

    return motion_data.motion_overview(
        joint=joint,
        prefix=f"""
{calibration_data.direction_name} {joint.name} {calibration_data.profile_name} Motion Profile: 
The  dynamic range has been exceeded. {backtracking_message}
""",
    )


def _get_next_travel_duration_in_seconds(
    calibration_data: TrajectoryCalibrationData,
    is_use_effort_for_dynamic_decrease: bool,
) -> tuple[float, float, str]:
    """
    This method figures our how much the next calibration step/run is going to change the travel duration by.

    Returns new_travel_duration, change_time_by and message
    """
    new_travel_duration = (
        calibration_data.calibration_targets.travel_duration_start_seconds
    )
    change_time_by = new_travel_duration

    good_travel_duration = (
        calibration_data.last_good_calibration.trajectory.travel_duration_seconds
        if calibration_data.last_good_calibration
        else None
    )
    bad_travel_duration = (
        calibration_data.last_bad_calibration.trajectory.travel_duration_seconds
        if calibration_data.last_bad_calibration
        else None
    )
    STOPPED_FOR_SAFETY_MOTION_FIXED_DECREASE = (
        calibration_data.calibration_targets.end_condition_time_step
    )

    if not good_travel_duration and not bad_travel_duration:
        return new_travel_duration, change_time_by, ""

    message = f"""New {calibration_data.direction_name} calibration step:"""

    if (
        not good_travel_duration
        and bad_travel_duration
        and calibration_data.last_bad_calibration
    ):
        # We've already overshot without finding a good value on the first run.
        # We could try to backtrack to find a good starting value, but we're going to error instead, for safety.
        raise ValueError(
            f"Bad initial travel duration in Calibration Targets. Started at {bad_travel_duration}s, achieiving {calibration_data.last_bad_calibration.linear_speed_cm_per_second}m/s, and faulted. Please review the Calibration Targets: {calibration_data.calibration_targets}"
        )

    if not good_travel_duration:
        raise ValueError("good_travel_duration should have a value here.")

    if (
        good_travel_duration
        and not bad_travel_duration
        and calibration_data.last_good_calibration
    ):
        # We need to speed up motion and decrease the time step:
        change_time_by = -1 * _get_dynamic_decrease_time_by(
            calibration_data=calibration_data,
            motion_data=calibration_data.last_good_calibration,
            is_use_effort_for_dynamic_decrease=is_use_effort_for_dynamic_decrease,
        )

        new_travel_duration = round(good_travel_duration + change_time_by, 2)

        message += f"""
    Decreasing the last travel time from {good_travel_duration}s to {new_travel_duration}s ({change_time_by:.2f}s) for this run.
"""

    if (
        good_travel_duration
        and bad_travel_duration
        and calibration_data.last_bad_calibration
        and calibration_data.last_good_calibration
    ):
        # We need to slow down motion and increase the time step:
        change_time_by = (good_travel_duration - bad_travel_duration) / 2

        if calibration_data.last_motion_stopped_for_safety:
            change_time_by -= STOPPED_FOR_SAFETY_MOTION_FIXED_DECREASE

        new_travel_duration = round(good_travel_duration - change_time_by, 2)

        stopped_for_safety_message = ""
        if calibration_data.last_motion_stopped_for_safety:
            stopped_for_safety_message = (
                "NOTE: The last run motion was stopped for safety."
            )

        message += f"""
    Increasing the last travel time from {bad_travel_duration}s to {new_travel_duration}s ({change_time_by}s) for this run.
    The last known good travel time is {good_travel_duration}s. {stopped_for_safety_message}
"""

    if new_travel_duration <= 1.0:
        # Can't have travel duration go below zero. For safety, if it's below 1, we're done going to assume we're done.
        new_travel_duration: float = good_travel_duration
        change_time_by = 0
        message = f"""
    Cannot decrease the travel time below {new_travel_duration}. This will be taken as the optimal value.
"""

    return new_travel_duration, change_time_by, message


def _check_runstop():
    pimu.pull_status()
    is_runstopped = pimu.status["runstop_event"]
    if is_runstopped:
        while is_runstopped:
            pimu.pull_status()
            is_runstopped = pimu.status["runstop_event"]

            print(
                f"Runstopped, waiting to resume. {BatteryInfo.get_battery_info(pimu)}"
            )

            time.sleep(3)
        return True
    return False


def _step_calibration(
    calibration_data: TrajectoryCalibrationData,
    joint: "PrismaticJoint|Base",
    disable_guarded_mode: bool,
    disable_dynamic_limits: bool,
    trajectory: TrajectoryFlattened | None = None,
) -> bool:
    """
    Decreases the `current_travel_duration` until one of the `MotionData::is_exceeded_calibration_targets()` conditions is met.

    Note: calling `_step_calibration()` after calibration is completed for this movement direction will use the best calibration values to move the joint, but will not collect new data.

    Returns `False` if there is no new motion data generated.
    """

    _check_runstop()

    # Set the motion trajectory:
    trajectory_to_run = trajectory
    if trajectory_to_run is None:
        travel_duration, change_time_by, message = _get_next_travel_duration_in_seconds(
            calibration_data=calibration_data, is_use_effort_for_dynamic_decrease=True
        )

        end_condition_1 = (
            calibration_data.last_bad_calibration
            and abs(change_time_by)
            < calibration_data.calibration_targets.end_condition_time_step
            and not calibration_data.last_motion_stopped_for_safety
        )
        end_condition_2 = (
            change_time_by == 0
        )  # If we're not changing the travel duration at all, we don't need to continue.

        if calibration_data.last_good_calibration and (
            end_condition_1 or end_condition_2
        ):
            # we're close enough, accept this motion_data as optimal
            calibration_data.optimal_calibration_motion_data = (
                calibration_data.last_good_calibration
            )
            calibration_data.optimal_calibration_motion_data.step_calibration_result = (
                StepCalibrationResult.TARGET_REACHED
            )

            # don't change the travel duration for the next run.
            travel_duration = (
                calibration_data.last_good_calibration.trajectory.travel_duration_seconds
            )
        else:
            print(message)

        if not isinstance(joint, Base):
            trajectory_to_run = _get_trajectory_based_on_joint_limits(
                joint=joint,
                is_positive_direction=calibration_data.is_positive_direction,
                travel_duration=travel_duration,
                is_use_velocity=calibration_data.is_use_velocity,
                is_use_acceleration=calibration_data.is_use_acceleration,
                offset_from_joint_limit_min=calibration_data.calibration_targets.offset_from_joint_limit_min,
                offset_from_joint_limit_max=calibration_data.calibration_targets.offset_from_joint_limit_max,
            )
        else:
            trajectory_to_run = _get_trajectory_diff_drive(
                is_positive_direction=calibration_data.is_positive_direction,
                travel_duration=travel_duration,
                is_use_velocity=calibration_data.is_use_velocity,
                is_use_acceleration=calibration_data.is_use_acceleration,
                offset_from_joint_limit_min=calibration_data.calibration_targets.offset_from_joint_limit_min,
                offset_from_joint_limit_max=calibration_data.calibration_targets.offset_from_joint_limit_max,
            )

    # Run the motion and collect motion data:
    motion_data = run_profile_trajectory(
        joint=joint,
        trajectory=trajectory_to_run,
        calibration_targets=calibration_data.calibration_targets,
        disable_guarded_mode=disable_guarded_mode,
        disable_dynamic_limits=disable_dynamic_limits,
    )

    if calibration_data.is_calibrated():
        print(
            f"\n    The {calibration_data.direction_name} dynamic range is already calibrated, but step_calibration did the motion anyway.\n"
        )
        return False

    if _check_runstop():
        # If the robot is runstopped, we'll mark this step as a bad step
        print(
            "\nWARNING: Marking the step as a bad step because the runstop button was pressed. If this was not intentional, please restart the calibration.\n"
        )
        motion_data.is_motion_stopped_for_safety = True

    calibration_data.last_motion_stopped_for_safety = (
        motion_data.is_motion_stopped_for_safety
    )

    if motion_data.is_motion_stopped_for_safety and isinstance(joint, Base):
        # Try to move the robot where it was supposed to end up.
        distance = (
            motion_data.trajectory.positions[-1]
            - motion_data.positions_during_motion[-1]
        )
        if abs(distance) > 0:
            joint.translate_by(distance)
            joint.push_command()
            joint.wait_until_at_setpoint()

    message = ""

    if (
        not motion_data.is_exceeded_calibration_targets()
        and not motion_data.is_motion_stopped_for_safety
    ):
        message = _good_step(
            calibration_data=calibration_data, motion_data=motion_data, joint=joint
        )
    else:
        message = _bad_step(
            calibration_data=calibration_data, motion_data=motion_data, joint=joint
        )

    calibration_data.messages.append(message)

    print(message)

    return True


def _do_calibration_trajectory_mode_dynamic_limits(
    joint: "PrismaticJoint|Base",
    is_use_velocity: bool,
    is_use_acceleration: bool,
    filename_prefix: str,
    motion_type: MotionProfileTypes,
    positive_calibration_targets: CalibrationTargets,
    negative_calibration_targets: CalibrationTargets,
) -> tuple[TrajectoryCalibrationData, TrajectoryCalibrationData]:
    """
    Uses trajectory mode to construct paths, to dynamically calibrate dynamic limits for your robot's joint.

    NOTE: guarded contact limits will be disabled for this calibration, and this code will monitor current draw (effort) directly.

    See `calibration_trajectory_mode_dynamic_limits()` for more information
    """

    battery_info = BatteryInfo.get_battery_info(pimu)
    print(battery_info)

    positive_motion = TrajectoryCalibrationData(
        description=f"{joint.name} Positive",
        motion_type=motion_type,
        battery_info=battery_info,
        is_positive_direction=True,
        is_use_velocity=is_use_velocity,
        is_use_acceleration=is_use_acceleration,
        calibration_targets=positive_calibration_targets,
    )
    negative_motion = TrajectoryCalibrationData(
        description=f"{joint.name} Negative",
        motion_type=motion_type,
        battery_info=battery_info,
        is_positive_direction=False,
        is_use_velocity=is_use_velocity,
        is_use_acceleration=is_use_acceleration,
        calibration_targets=negative_calibration_targets,
    )

    while not positive_motion.is_calibrated() or not negative_motion.is_calibrated():

        new_motion_to_plot = _step_calibration(
            calibration_data=positive_motion,
            joint=joint,
            disable_guarded_mode=True,
            disable_dynamic_limits=True,
        )

        if new_motion_to_plot:
            _plot_motion_profiles_and_save_outputs(
                calibration_data=positive_motion,
                motion_data=positive_motion.motion_data[-1],
                filename_prefix=filename_prefix,
            )

        new_motion_to_plot = _step_calibration(
            calibration_data=negative_motion,
            joint=joint,
            disable_guarded_mode=True,
            disable_dynamic_limits=True,
        )

        if new_motion_to_plot:
            _plot_motion_profiles_and_save_outputs(
                calibration_data=negative_motion,
                motion_data=negative_motion.motion_data[-1],
                filename_prefix=filename_prefix,
            )

    # Save and print optimal motion profile data:

    optimal_positive = positive_motion.optimal_calibration_motion_data
    optimal_negative = negative_motion.optimal_calibration_motion_data
    if optimal_positive is None or optimal_negative is None:
        raise Exception("Calibration failed.")

    _plot_motion_profiles_and_save_outputs(
        calibration_data=positive_motion,
        motion_data=optimal_positive,
        filename_prefix="optimal_" + filename_prefix,
    )
    _plot_motion_profiles_and_save_outputs(
        calibration_data=negative_motion,
        motion_data=optimal_negative,
        filename_prefix="optimal_" + filename_prefix,
    )

    print(
        f"""
Optimal Positive {joint.name} {positive_motion.profile_name} Motion Profile: 
{optimal_positive.motion_overview(joint=joint)}

Optimal Negative {joint.name} {negative_motion.profile_name} Motion Profile: 
{optimal_negative.motion_overview(joint=joint)}
"""
    )

    return (positive_motion, negative_motion)


def run_dynamic_limit_calibration(
    joint: "PrismaticJoint|Base", label: str
) -> list[TrajectoryCalibrationData]:
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
        motion_type=MotionProfileTypes.linear,
        is_use_velocity=False,
        is_use_acceleration=False,
        filename_prefix=filename_prefix,
        positive_calibration_targets=CalibrationTargets.linear_default(joint),
        negative_calibration_targets=CalibrationTargets.linear_default(joint),
    )
    tictoc_timer("Linear Calibration")

    # Cubic:
    tictoc_timer("Cubic Calibration")
    results_cubic = _do_calibration_trajectory_mode_dynamic_limits(
        joint=joint,
        motion_type=MotionProfileTypes.cubic,
        is_use_velocity=True,
        is_use_acceleration=False,
        filename_prefix=filename_prefix,
        positive_calibration_targets=CalibrationTargets.cubic_default(joint),
        negative_calibration_targets=CalibrationTargets.cubic_default(joint),
    )
    tictoc_timer("Cubic Calibration")

    # Quintic:
    tictoc_timer("Quintic Calibration")
    results_quintic = _do_calibration_trajectory_mode_dynamic_limits(
        joint=joint,
        motion_type=MotionProfileTypes.quintic,
        is_use_velocity=True,
        is_use_acceleration=True,
        filename_prefix=filename_prefix,
        positive_calibration_targets=CalibrationTargets.quintic_default(joint),
        negative_calibration_targets=CalibrationTargets.quintic_default(joint),
    )
    tictoc_timer("Quintic Calibration")

    return [
        results_linear[0],
        results_linear[1],
        results_cubic[0],
        results_cubic[1],
        results_quintic[0],
        results_quintic[1],
    ]


def _print_calibration_trajectory_efforts(
    joint: "PrismaticJoint|Base",
    calibration_data: TrajectoryCalibrationData,
):

    # Save and print optimal motion profile data:
    max_efforts = [
        motion_data.effort_percent_max_absolute
        for motion_data in calibration_data.motion_data
    ]
    overview = "\n".join(
        [
            motion_data.motion_overview(joint=joint)
            for motion_data in calibration_data.motion_data
        ]
    )
    direction_text = (
        "Positive" if calibration_data.is_positive_direction else "Negative"
    )
    print(
        f"""
{direction_text} {joint.name} {calibration_data.profile_name} Motion Profile Overview:
Max efforts: {max_efforts}, Average effort: {np.average(max_efforts)}%
The following are the overviews for the {direction_text} run(s):
{overview}

-----------
"""
    )


def _do_calibration_trajectory_efforts(
    joint: "PrismaticJoint|Base",
    motion_type: MotionProfileTypes,
    is_use_velocity: bool,
    is_use_acceleration: bool,
    filename_prefix: str,
    positive_calibration_targets: CalibrationTargets,
    negative_calibration_targets: CalibrationTargets,
) -> tuple[TrajectoryCalibrationData, TrajectoryCalibrationData]:
    """
    Uses trajectory mode to construct paths, to dynamically calibrate dynamic limits for your robot's joint.

    NOTE: guarded contact limits will be disabled for this calibration, and this code will monitor current draw (effort) directly.

    See `calibration_trajectory_mode_dynamic_limits()` for more information
    """

    battery_info = BatteryInfo.get_battery_info(pimu)
    print(battery_info)

    positive_motion = TrajectoryCalibrationData(
        description=f"{joint.name} Positive",
        motion_type=motion_type,
        battery_info=battery_info,
        is_positive_direction=True,
        is_use_velocity=is_use_velocity,
        is_use_acceleration=is_use_acceleration,
        calibration_targets=positive_calibration_targets,
    )
    negative_motion = TrajectoryCalibrationData(
        description=f"{joint.name} Negative",
        motion_type=motion_type,
        battery_info=battery_info,
        is_positive_direction=False,
        is_use_velocity=is_use_velocity,
        is_use_acceleration=is_use_acceleration,
        calibration_targets=negative_calibration_targets,
    )

    for _ in range(args.ncycle):

        new_motion_to_plot = _step_calibration(
            calibration_data=positive_motion,
            joint=joint,
            disable_guarded_mode=False,
            disable_dynamic_limits=False,
            trajectory=(
                positive_motion.motion_data[-1].trajectory
                if positive_motion.motion_data
                else None
            ),
        )

        if new_motion_to_plot:
            _plot_motion_profiles_and_save_outputs(
                calibration_data=positive_motion,
                motion_data=positive_motion.motion_data[-1],
                filename_prefix=filename_prefix,
            )

        new_motion_to_plot = _step_calibration(
            calibration_data=negative_motion,
            joint=joint,
            disable_guarded_mode=False,
            disable_dynamic_limits=False,
            trajectory=(
                negative_motion.motion_data[-1].trajectory
                if negative_motion.motion_data
                else None
            ),
        )

        if new_motion_to_plot:
            _plot_motion_profiles_and_save_outputs(
                calibration_data=negative_motion,
                motion_data=negative_motion.motion_data[-1],
                filename_prefix=filename_prefix,
            )

    _print_calibration_trajectory_efforts(joint=joint, calibration_data=positive_motion)
    _print_calibration_trajectory_efforts(joint=joint, calibration_data=negative_motion)

    return (positive_motion, negative_motion)


def run_trajectory_effort_calibration(
    joint: "PrismaticJoint|Base", label: str
) -> list[TrajectoryCalibrationData]:
    """
    Uses trajectory mode to figure out the average effort for a trajectory for your robot.

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

    linear_calibration_targets = CalibrationTargets.linear_default(joint)
    linear_calibration_targets.travel_duration_start_seconds += (
        2  # Slow it down for this test.
    )
    cubic_calibration_targets = CalibrationTargets.cubic_default(joint)
    cubic_calibration_targets.travel_duration_start_seconds += (
        2  # Slow it down for this test.
    )
    quintic_calibration_targets = CalibrationTargets.quintic_default(joint)
    quintic_calibration_targets.travel_duration_start_seconds += (
        2  # Slow it down for this test.
    )

    # Linear:
    tictoc_timer("Linear Calibration")
    results_linear = _do_calibration_trajectory_efforts(
        joint=joint,
        motion_type=MotionProfileTypes.linear,
        is_use_velocity=False,
        is_use_acceleration=False,
        filename_prefix=filename_prefix,
        negative_calibration_targets=linear_calibration_targets,
        positive_calibration_targets=linear_calibration_targets,
    )
    tictoc_timer("Linear Calibration")

    # Cubic:
    tictoc_timer("Cubic Calibration")
    results_cubic = _do_calibration_trajectory_efforts(
        joint=joint,
        motion_type=MotionProfileTypes.cubic,
        is_use_velocity=True,
        is_use_acceleration=False,
        filename_prefix=filename_prefix,
        positive_calibration_targets=cubic_calibration_targets,
        negative_calibration_targets=cubic_calibration_targets,
    )
    tictoc_timer("Cubic Calibration")

    # Quintic:
    tictoc_timer("Quintic Calibration")
    results_quintic = _do_calibration_trajectory_efforts(
        joint=joint,
        motion_type=MotionProfileTypes.quintic,
        is_use_velocity=True,
        is_use_acceleration=True,
        filename_prefix=filename_prefix,
        positive_calibration_targets=quintic_calibration_targets,
        negative_calibration_targets=quintic_calibration_targets,
    )
    tictoc_timer("Quintic Calibration")

    return [
        results_linear[0],
        results_linear[1],
        results_cubic[0],
        results_cubic[1],
        results_quintic[0],
        results_quintic[1],
    ]


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


def _run_dynamic_limits_calibration(
    joint: "PrismaticJoint|Base",
) -> list[TrajectoryCalibrationData]:
    """
    Entry point for running Dynamic Limits Calibration.
    """
    global trajectory_folder_to_save_plots

    trajectory_folder_to_save_plots = get_stretch_directory(
        f"calibration_trajectory_dynamic_limits/{int(time.time())}"
    )

    os.system("mkdir -p " + trajectory_folder_to_save_plots)

    print(f"Writing to {trajectory_folder_to_save_plots}")

    tictoc_timer("Calibration Trajectory")

    robot_name = __import__("platform").node()  # get computer name
    label = f"{robot_name}_{round(time.time()*1000)}"

    results = run_dynamic_limit_calibration(joint, label=label)

    tictoc_timer("Calibration Trajectory")

    return results


def _run_trajectory_efforts_calibration(
    joint: "PrismaticJoint|Base",
) -> list[TrajectoryCalibrationData]:
    """
    Run Trajectory Effort calibration then print results.
    """
    global trajectory_folder_to_save_plots

    trajectory_folder_to_save_plots = get_stretch_directory(
        f"calibration_trajectory_efforts/{int(time.time())}"
    )

    os.system("mkdir -p " + trajectory_folder_to_save_plots)

    print(f"Writing to {trajectory_folder_to_save_plots}")

    tictoc_timer("Calibration Trajectory")

    robot_name = __import__("platform").node()  # get computer name
    label = f"{robot_name}_{round(time.time()*1000)}"

    results = run_trajectory_effort_calibration(joint, label=label)

    print(
        """
Trajectory calibration results:
          
"""
    )

    for calibration_data in results:
        _print_calibration_trajectory_efforts(
            joint=joint, calibration_data=calibration_data
        )

    tictoc_timer("Calibration Trajectory")

    return results


def _disable_sync_mode(joint: "PrismaticJoint|Base"):
    if not isinstance(joint, Base):
        joint.motor.disable_sync_mode()
    else:
        joint.left_wheel.disable_sync_mode()
        joint.right_wheel.disable_sync_mode()

    joint.push_command()


def _disable_guarded_mode(joint: "PrismaticJoint|Base"):
    if not isinstance(joint, Base):
        joint.motor.disable_guarded_mode()
    else:
        joint.left_wheel.disable_guarded_mode()
        joint.right_wheel.disable_guarded_mode()

    joint.push_command()


def _enable_safety(joint: "PrismaticJoint|Base"):
    if not isinstance(joint, Base):
        joint.motor.enable_safety()
    else:
        joint.left_wheel.enable_safety()
        joint.right_wheel.enable_safety()

    joint.push_command()
    joint.stop_trajectory()
    joint.push_command()
    joint.pull_status()


def _follow_trajectory(joint: "PrismaticJoint|Base"):
    if not isinstance(joint, Base):
        return joint.follow_trajectory(move_to_start_point=True)
    else:
        return joint.follow_trajectory()


def _is_homed(joint: "PrismaticJoint|Base"):
    joint.pull_status()
    if not isinstance(joint, Base):
        return joint.motor.status["pos_calibrated"]
    else:
        # return joint.left_wheel.status["pos_calibrated"] and joint.right_wheel.status["pos_calibrated"]
        return True


def _idle_wait_for_battery(target_voltage: float) -> float:
    """
    Wait for battery to reach a target
    """

    battery_voltage = BatteryInfo.get_battery_info(pimu).battery_voltage

    node = subprocess.Popen(["ros2", "launch", "stretch_core", "rplidar.launch.py"])
    node2 = subprocess.Popen(
        ["ros2", "launch", "stretch_core", "d435i_high_resolution.launch.py"]
    )

    while target_voltage < battery_voltage:
        battery_voltage = BatteryInfo.get_battery_info(pimu).battery_voltage
        print(
            f"Idling while waiting for battery to reach {target_voltage}. Currently: {battery_voltage}"
        )

        time.sleep(30)

    node.kill()
    node2.kill()

    return battery_voltage


class _RunMode(IntEnum):
    dynamic_limit_mode = 0
    trajectory_effort_mode = 1

    def run(self, joint: "PrismaticJoint|Base") -> list[TrajectoryCalibrationData]:
        if self == _RunMode.dynamic_limit_mode:
            return _run_dynamic_limits_calibration(joint)
        if self == _RunMode.trajectory_effort_mode:
            return _run_trajectory_efforts_calibration(joint)

        raise NotImplementedError("This mode is not implemented.")


def _write_dynamic_limits_config_config(
    joint: "PrismaticJoint|Base", calibration_data: TrajectoryCalibrationData
):
    """
    Writes dynamic limits to stretch_user/[robot_name]/stretch_configuration_params.yaml
    """
    motion_type = calibration_data.motion_type.name
    direction = "positive" if calibration_data.is_positive_direction else "negative"

    joint.write_configuration_param_to_YAML(
        f"{joint.name}.motion.trajectory_max.{motion_type}.{direction}.vel_m",
        calibration_data.get_optimal_calibration_motion_data().current_linear_speed_meters_per_second(is_round=False),
        force_creation=True,
    )
    joint.write_configuration_param_to_YAML(
        f"{joint.name}.motion.trajectory_max.{motion_type}.{direction}.accel_m",
        calibration_data.get_optimal_calibration_motion_data().max_acceletation_during_motion,
        force_creation=True,
    )

    # Write effort threshold for contacts:
    effort = calibration_data.get_optimal_calibration_motion_data().calibration_targets.effort_percent_target
    joint.write_configuration_param_to_YAML(
        f"{joint.name}.contact_models.effort_pct.contact_thresh_default",
        [-effort, effort],
        force_creation=True,
    )


def save_calibrated_dynamic_limits_to_config(
    joint: "PrismaticJoint|Base",
    calibration_data: list[TrajectoryCalibrationData],
    skip_confirm: bool = False
):
    log_dir = get_stretch_directory("log/")
    log_file_ts = create_time_string()
    log_file_prefix = f"calibrate_trajectory_limits_{joint.name}"

    confirm_text = [f"{'Positive' if calibration.is_positive_direction else 'Negative'} {calibration.motion_type.name.capitalize()}" for calibration in calibration_data]
    if skip_confirm or click.confirm(f"Save results for {','.join(confirm_text)} dynamic calibration limits?"):
        
        log_filename = log_dir + log_file_prefix + "_results_" + log_file_ts + ".log"
        print("Writing results log: %s" % log_filename)
        log_output = ""
        
        for calibration in calibration_data:
            _write_dynamic_limits_config_config(joint, calibration)

            log_output += f"""
{calibration.motion_type.name}:
Optimal {'Positive' if calibration.is_positive_direction else 'Negative'} {joint.name} {calibration.profile_name} Motion Profile: 
{calibration.get_optimal_calibration_motion_data().motion_overview(joint=joint)}
"""

        with open(log_filename, "w") as log_file:
            log_file.write(log_output)


if __name__ == "__main__":
    print_stretch_re_use()

    parser = argparse.ArgumentParser(
        description="Calibrate the linear, cubic and quintic trajectory dynamic limits or the trajectory effort of a joint."
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--lift", help="Calibrate the lift joint", action="store_true")
    group.add_argument("--arm", help="Calibrate the arm joint", action="store_true")
    group.add_argument("--base", help="Calibrate the base joint", action="store_true")

    group2 = parser.add_mutually_exclusive_group(required=False)
    group2.add_argument(
        "--dynamic_limit_mode",
        help="Calibrate the joint to test its dynamic limits",
        action="store_true",
    )
    group2.add_argument(
        "--trajectory_effort_mode",
        help="Find the linear, cubic and quintic motion profile efforts for your robot.",
        action="store_true",
    )
    parser.add_argument(
        "--ncycle", type=int, help="Number of sweeps to run. Applies to trajectory_effort_mode only. [4]", default=4
    )
    parser.add_argument("--skip_homing", help="Skip joint homing", action="store_true")
    parser.add_argument(
        "--run_continously_until_battery_low",
        help="Runs calibration continuously until the battery is low.",
        action="store_true",
    )
    args = parser.parse_args()

    if not args.skip_homing:
        click.secho(
            "The Lift, Arm and Wrist yaw will need to be first homed. Ensure workspace is collision free.",
            fg="yellow",
        )
        if not click.confirm("Proceed?", default=True):
            exit(0)

        subprocess.call(
            "stretch_lift_home.py"
        )  # Home the lift first to avoid the arm slamming into the ground at lift=0
        subprocess.call("stretch_arm_home.py")
        subprocess.call("stretch_wrist_yaw_home.py")

    if not (args.dynamic_limit_mode or args.trajectory_effort_mode):
        run_choices = "".join([f"{mode.name}[{mode.value}]\n" for mode in _RunMode])
        run_mode = _RunMode(
            int(
                click.prompt(
                    f"""Choose the type of calibration you want to do: 
{run_choices}""",
                    type=click.Choice([f"{mode.value}" for mode in _RunMode]),
                    show_choices=False,
                )
            )
        )
    else:
        run_mode = _RunMode.dynamic_limit_mode
        if args.trajectory_effort_mode:
            run_mode = _RunMode.trajectory_effort_mode

    if not (args.arm or args.lift or args.arm):
        joint_choices = "".join(
            [
                f"{j.name}[{j.value}]\n"
                for j in JointTypes.available_joints(run_mode=run_mode)
            ]
        )
        joint_type = JointTypes(
            int(
                click.prompt(
                    f"""
Choose the joint to run the calibration on: 
{joint_choices}""",
                    type=click.Choice(
                        [
                            f"{j.value}"
                            for j in JointTypes.available_joints(run_mode=run_mode)
                        ]
                    ),
                    show_choices=False,
                )
            )
        )
    else:
        joint_type = JointTypes.lift
        if args.arm:
            joint_type = JointTypes.arm
        if args.base:
            joint_type = JointTypes.base

    if joint_type == JointTypes.base and not click.confirm(
        "The base calibration is experimental. Keep the robot on a level surface. Be careful, the base may drift during calibration. Proceed?",
        default=True,
    ):
        exit(1)

    _joint = joint_type.get_joint_instance()

    if not isinstance(_joint, Base):
        # Skip contact sensing for base:
        check_deprecated_contact_model_prismatic_joint(
            _joint, "REx_calibrate_guarded_contacts.py", None, None, None, None
        )

    if not _joint.startup(threaded=False):
        exit(1)

    if not _is_homed(_joint):
        print("Joint not calibrated. Exiting.")
        exit(1)

    pimu = Pimu()
    if not pimu.startup(threaded=False):
        print("Could not start the PIMU")
        exit(1)

    pimu.pull_status()

    if (run_mode is _RunMode.dynamic_limit_mode):
        click.secho("------------------------", fg="yellow")
        click.secho(
            "NOTE: This tool updates motion.trajectory_max for %s in stretch_configuration_params.yaml"
            % _joint.name.upper(),
            fg="yellow",
        )
        click.secho(
            "NOTE: Your stretch_user_params.yaml overrides dynamic motion.trajectory_max for %s"
            % _joint.name.upper(),
            fg="yellow",
        )
        click.secho(
            "NOTE: As such, the updated calibration will not change the contact behavior unless you remove the user params.",
            fg="yellow",
        )
    click.secho("------------------------", fg="yellow")

    click.secho(
        """
Joint %s will go through its full range-of-motion (up to 1m).
1. Ensure workspace is collision free
2. Dynamic limits will be significantly increased - effectively disabled - for the duration of this test, be careful!
3. The lift or joints may suddenly accelerate and/or freefall. Safety measures are in place to brake the motors, however, still be careful!

Note: If you get a matplotlib related error when running this script, please run `export QT_QPA_PLATFORM_PLUGIN_PATH='/usr/lib/x86_64-linux-gnu/qt5/plugins/platforms/libqxcb.so'`
"""
        % _joint.name.capitalize(),
        fg="yellow",
    )
    if click.confirm("Proceed?", default=True):

        if args.run_continously_until_battery_low:
            current_voltage = BatteryInfo.get_battery_info(pimu).battery_voltage
            targets = np.arange(11.5, current_voltage, 0.5)[::-1]
            click.secho(
                f"""

Running continiously until the is battery low. Step targets: {targets}V. Current voltage: {current_voltage}V.

Note: while the robot is idling, the rplidar and camera will be turned on to consume power more quickly.
        """,
                fg="yellow",
            )

            ask_for_confirmation = click.confirm(
                f"Do you want to manually kick off the calibration when the next voltage target is reached? Choosing NO will automatically start the joint motion when the target voltage is reached.",
                default=False,
            )

            if ask_for_confirmation:
                print(
                    "You will be asked for confirmation when the correct voltage target is reached."
                )

            results = None

            if click.confirm(
                f"Run calibration immediately? Choosing NO will wait until the next target {targets[0]}V to start."
            ):
                results = run_mode.run(_joint)

            for target_voltage in targets:
                current_voltage = _idle_wait_for_battery(target_voltage=target_voltage)

                if ask_for_confirmation and not click.confirm(
                    f"Battery voltage {current_voltage} (need {target_voltage}) is sufficient. Start?",
                    default=True,
                ):
                    exit(1)

                print("Target battery voltage reached, starting calibration.")

                results = run_mode.run(_joint)

            # Ask to save config if they're running the dynamic limit mode:
            if results:
                save_calibrated_dynamic_limits_to_config(_joint, results)

            exit(0)

        results = run_mode.run(_joint)

        if run_mode is _RunMode.dynamic_limit_mode and results:
            # Ask to save config if they're running the dynamic limit mode:
            save_calibrated_dynamic_limits_to_config(_joint, results)
