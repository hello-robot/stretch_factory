import json
import os
import unittest


from python.tools.REx_calibrate_trajectory_limits import JointTypes, MotionProfileTypes, TrajectoryCalibrationData, save_calibrated_dynamic_limits_to_config

test_dir = os.path.dirname(os.path.abspath(__file__))

class TestCalibrateTrajectoryLiimts(unittest.TestCase):
    def test_save_config(self):
        calibration_data = []
        for motion_type in MotionProfileTypes:
            for direction in ("positive", "negative"):
                with open(f"{test_dir}/stubs/calibrate_trajectory_limits/arm_{direction}_{motion_type.name}.json", "r") as fp:
                    calibration_data.append(
                        TrajectoryCalibrationData.from_json(
                    json.load(fp)
                        )
                    )
        
        save_calibrated_dynamic_limits_to_config(joint=JointTypes.arm.get_joint_instance(), calibration_data=calibration_data, skip_confirm=True)
       

