![](./images/banner.png)
# Overview

The Stretch Factory package provides low-level Python tools for debug, testing,  and calibration of the Hello Robot Stretch RE1. 

**These tools are provided for reference only and are intended to be used under the guidance of Hello Robot support engineers.** 

This package can be installed by:

```
pip2 install  hello-robot-stretch-factory
```

The available Stretch Factory tools can be found by tab completing after typing 'RE1_'. For example:
```bash
RE1_base_calibrate_imu_collect.py         RE1_dynamixel_reboot.py                   RE1_stepper_calibration_YAML_to_flash.py
RE1_base_calibrate_imu_process.py         RE1_dynamixel_set_baud.py                 RE1_stepper_jog.py
RE1_base_calibrate_wheel_separation.py    RE1_firmware_updater.py                   RE1_stepper_mechaduino_menu.py
RE1_cliff_sensor_calibrate.py             RE1_gripper_calibrate.py                  RE1_timestamp_manager_analyze.py
RE1_clock_manager_analyze.py              RE1_head_calibrate_pan.py                 RE1_usb_reset.py
RE1_dynamixel_id_change.py                RE1_hello_dynamixel_jog.py                RE1_wacc_calibrate.py
RE1_dynamixel_id_scan.py                  RE1_stepper_calibration_flash_to_YAML.py  
RE1_dynamixel_jog.py                      RE1_stepper_calibration_run.py            

```
