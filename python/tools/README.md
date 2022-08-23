# Stretch Factory Tools

The list of tools can be found by tab completion of 'RE' at the command line:

```bash
>>$ RE

RE1_base_calibrate_imu_collect.py         RE1_D435i_check.py                        RE1_dynamixel_jog.py                      RE1_gamepad_configure.py                  RE1_stepper_calibration_flash_to_YAML.py  RE1_stepper_mechaduino_menu.py
RE1_base_calibrate_imu_process.py         RE1_dynamixel_calibrate_range.py          RE1_dynamixel_reboot.py                   RE1_gripper_calibrate.py                  RE1_stepper_calibration_run.py            RE1_usb_reset.py
RE1_base_calibrate_wheel_separation.py    RE1_dynamixel_id_change.py                RE1_dynamixel_set_baud.py                 RE1_hello_dynamixel_jog.py                RE1_stepper_calibration_YAML_to_flash.py  RE1_wacc_calibrate.py
RE1_cliff_sensor_calibrate.py             RE1_dynamixel_id_scan.py                  RE1_firmware_updater.py                   RE1_migrate_params.py                     RE1_stepper_jog.py                        README.md
```

These tools are used during the factory system 'bringup' of the robot. They are organized by subsystem:

* REx_arm*
* REx_base*
* REx_dynamixel*
* REx_lift*
* REx_stepper*
* REx_wacc*

The tools will generally interact with the lowest level interface of the hardware, make measurements, and write calibration data to the robot's YAML or devices EEPROM. For example, the following script calibrates the wrist accelerometer such that the gravity term is 9.8m/s^2.

```bash
>>$ REx_wacc_calibrate_gravity.py
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

