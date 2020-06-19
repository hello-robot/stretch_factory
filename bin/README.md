# Stretch Factory Tools

The list of tools can be found by tab completion of 'RE1' at the command line:

```bash
>>$ RE1_
RE1_arm_calibrate_force.py                RE1_base_calibrate_imu_process.py         RE1_lift_calibrate_force.py               RE1_stepper_calibration_YAML_to_flash.py
RE1_arm_calibrate_guarded_contact.py      RE1_base_tune_ctrl.py                     RE1_lift_calibrate_guarded_contact.py     RE1_stepper_jog.py
RE1_arm_calibrate_range.py                RE1_dynamixel_id_change.py                RE1_lift_calibrate_range.py               RE1_stepper_load_test.py
RE1_arm_tune_ctrl.py                      RE1_dynamixel_id_scan.py                  RE1_lift_tune_ctrl.py                     RE1_stepper_mechaduino_menu.py
RE1_base_calibrate_cliff.py               RE1_dynamixel_jog.py                      RE1_stepper_board_reset.py                RE1_stepper_tune_ctrl.py
RE1_base_calibrate_force.py               RE1_dynamixel_reboot.py                   RE1_stepper_calibration_flash_to_YAML.py  RE1_wacc_calibrate_gravity.py
RE1_base_calibrate_imu_collect.py         RE1_gripper_calibrate.py                  RE1_stepper_calibration_run.py  
```

These tools are used during the factory system 'bringup' of the robot. They are organized by subsystem:

* RE1_arm*
* RE1_base*
* RE1_dynamixel*
* RE1_lift*
* RE1_stepper*
* RE1_wacc*

The tools will generally interact with the lowest level interface of the hardware, make measurements, and write calibration data to the robot's YAML or devices EEPROM. For example, the following script calibrates the wrist accelerometer such that the gravity term is 9.8m/s^2.

```bash
>>$ RE1_wacc_calibrate_gravity.py
Ensure base is level and arm is retracted. Hit enter when ready

Itr 0 Val 9.32055700006
...
Itr 99 Val 9.34092651895
Got a average value of 9.29669019184
Scalar of 1.05485391012
Write parameters to stretch_re1_factory_params.yaml (y/n)? [y]
y
Writing yaml...
```

**Caution: It is possible to break your robot by running these tools.** If not used properly these tools may not respect joint torque and position limits. They may overwrite existing calibration data as well. 

