# Changelog

The changes between releases of Stretch Factory is documented here.

## [0.5.3](https://github.com/hello-robot/stretch_factory/pull/89) - Feburary 3, 2024
This release adds a new tool `REx_camera_set_symlink.py` that allows the user create a USB symlink to any USB camera that is plugged into the robot. The symlink is assigned by generating an Udev rule that records the following USB attributes of the plugged in camera: `[idVendor,idProduct,serial]`.

Example Usage:
By addressing a camera port:
```bash
$ REx_camera_set_symlink.py --port /dev/video6 --symlink hello-new-camera
```
```bash
For use with S T R E T C H (R) from Hello Robot Inc.
---------------------------------------------------------------------

Linking usb port: /dev/video6 to symlink port: /dev/hello-new-camera
Successfully generated udev rule at path: /etc/udev/rules.d/86-hello-new-camera.rules
Successfully Identified device at port: /dev/hello-new-camera
```

## [0.5.2](https://github.com/hello-robot/stretch_factory/commit/a7df7e6cb8f617e2535738f23dac4c39dfca5eeb) - Feburary 2, 2024
There was a bug with the firmware updater tool, instead of before looking for the orginal dev/ttyACM port of the device when it is in bootloader state, it's been changed to look for the arduino zero device and use the associated dev/ttyACM port instead.

## [0.5.0](https://github.com/hello-robot/stretch_factory/pull/88) - January 24, 2024
This release introduces the concept of "stepper types" to the Stretch Factory package. In P5 firmware, we introduced the ability for the uC on a stepper PCB to know which kind of stepper it is (i.e. arm, lift, right wheel, left wheel). In this release, the firmware updater checks if the stepper already knows its stepper type before erasing the flash memory through a new firmware flash. It saves the stepper_type, flashes the new firmware, then writes the stepper_type to flash memory. This release also introduces the new tool called REx_stepper_type.py tool for Hello Robot support members to be able to assist Stretch users in flashing their stepper_type bits.

There's a couple benefits to each stepper knowing its stepper_type at the firmware level:

 1. The wheels on newer Stretch robots can take advantage of better runstop by actually disconnecting the H bridge from the motor. This makes it easier to backdrive the robot around by tilting the robot and pushing it like a vacuum cleaner.
 2. The system check tool can verify that the UDEV rules for each stepper agree with the stepper_type of the stepper. In case the UDEV rules get corrupted, this provides an additional level of redundancy.

## [0.4.13](https://github.com/hello-robot/stretch_factory/pull/73) - December 13, 2023
This release eliminates a failure case in the firmware updater where Hello devices are left in a soft-bricked (i.e. can be hardware reset) state from a failed firmware update attempt. The fix has been tested with 800+ firmware flashes on a variety of Stretch robots.

## [0.3.11](https://github.com/hello-robot/stretch_factory/pull/56) - January 17, 2023
This release adds the tool `REx_discover_hello_devices.py`. This tool will enable users to find and map all the robot-specific USB devices (i.e. Lift, Arm, Left wheel, Right wheel, Head, Wrist/End-of-arm) and assign them to the robot by updating UDEV rules and stretch configuration files. 
This tool would require Stretch Body v0.4.11 and above.

## [0.3.10](https://github.com/hello-robot/stretch_factory/compare/09d11fbef1972e08db8ae1599478fd4e399e4efa...f788900d89ba67d0e2f7aab342c1350b3736f3d0) - January 16, 2023
This release (and previous releases since 0.3.0) makes a number of small improvements to the following tools:

 - `REx_dynamixel_jog.py` - Jog tool can put dxl in multi-turn, position, pwm, and velocity modes
 - `REx_calibrate_range.py` - Add error checking for failed homing
 - `REx_calibrate_guarded_contact.py` - Support RE1 robots
 - `REx_base_calibrate_imu_collect.py` - Fix bug

There are also organization changes to the docs and READMEs.

## [0.3.0](https://github.com/hello-robot/stretch_factory/pull/52) - September 1, 2022
This release moves Stretch Factory to use a new naming scheme for its tools. The prefix `REx` is now used instead of `RE1`. This semantic change is in anticipation of the release of future versions of Stretch (e.g. RE2).

In addition, two new tools are introduced:

* REx_calibrate_guarded_contact.py: Measure the efforts required to move througout the joint workspace and save contact thresholds to Configuration YAML
* REx_calibrate_range.py: Measure the range of motion of a joint and save to the Configuration YAML.

These new tools move the the `effort_pct` contact model as supported by Stretch Body 0.3

Additional features;

* [Firmware updater tested and supports 20.04 #47](https://github.com/hello-robot/stretch_factory/pull/47)



## [0.2.0](https://github.com/hello-robot/stretch_factory/pull/45) - June 21, 2022
* [Support new parameter manage scheme #45](https://github.com/hello-robot/stretch_factory/pull/45)


Adds new parameter management format. This change will require older systems to migrate their parameters to the new format. For systems that haven't yet migrated, Stretch Body will exit with a warning that they must migrate first by running `RE1_migrate_params.py`. See the [forum post](https://forum.hello-robot.com/t/425) for more details.

## 0.1.0

* Introduce the RE1_firmware_update.py tool

## [0.0.2](https://github.com/hello-robot/stretch_factory/commit/9c44862c8f8cbaee534a603b1a22acfd042cefca) - May 13, 2020
This is the initial release of Stretch Factory. It includes tools to support debug and testing of the Stretch Hardware.

