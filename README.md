![](./docs/images/banner.png)
# Overview

The Stretch Factory package provides low-level Python tools for debug, testing,  and calibration of the Hello Robot Stretch RE1. 

**These tools are provided for reference only and are intended to be used under the guidance of Hello Robot support engineers.** 

This package can be installed by:

```
pip install  hello-robot-stretch-factory
```

The available Stretch Factory tools can be found by tab completing after typing 'REx_'. For example:
```bash
REx_base_calibrate_imu_collect.py         REx_dynamixel_reboot.py                   REx_stepper_calibration_YAML_to_flash.py
REx_base_calibrate_imu_process.py         REx_dynamixel_set_baud.py                 REx_stepper_jog.py
REx_base_calibrate_wheel_separation.py    REx_firmware_updater.py                   REx_stepper_mechaduino_menu.py
REx_cliff_sensor_calibrate.py             REx_gripper_calibrate.py                  REx_timestamp_manager_analyze.py
REx_clock_manager_analyze.py              REx_head_calibrate_pan.py                 REx_usb_reset.py
REx_dynamixel_id_change.py                REx_hello_dynamixel_jog.py                REx_wacc_calibrate.py
REx_dynamixel_id_scan.py                  REx_stepper_calibration_flash_to_YAML.py  
REx_dynamixel_jog.py                      REx_stepper_calibration_run.py            

```
For useage of these tools, try for example:

`REx_dynamixel_id_scan.py --help`

------
<div align="center"> All materials are Copyright 2022 by Hello Robot Inc. Hello Robot and Stretch are registered trademarks. The Stretch RE1 and RE2 robots are covered by U.S. Patent 11,230,000 and other patents pending.</div>

