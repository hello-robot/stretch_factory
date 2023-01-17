# Stretch Factory Tools

The list of tools can be found by tab completion of 'REx' at the command line:

```bash
>>$ REx

REx_base_calibrate_imu_collect.py         REx_D435i_check.py                        REx_dynamixel_set_baud.py                 REx_stepper_calibration_run.py            REx_usb_reset.py
REx_base_calibrate_imu_process.py         REx_discover_hello_devices.py             REx_firmware_updater.py                   REx_stepper_calibration_YAML_to_flash.py  REx_wacc_calibrate.py
REx_base_calibrate_wheel_separation.py    REx_dynamixel_id_change.py                REx_gamepad_configure.py                  REx_stepper_ctrl_tuning.py                
REx_calibrate_guarded_contact.py          REx_dynamixel_id_scan.py                  REx_gripper_calibrate.py                  REx_stepper_gains.py                      
REx_calibrate_range.py                    REx_dynamixel_jog.py                      REx_hello_dynamixel_jog.py                REx_stepper_jog.py                        
REx_cliff_sensor_calibrate.py             REx_dynamixel_reboot.py                   REx_stepper_calibration_flash_to_YAML.py  REx_stepper_mechaduino_menu.py 

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

