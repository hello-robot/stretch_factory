

# 009_STEPPER_STARTUP

### **Background**

A bug exists on earlier Stretch RE1 related to the startup conditions of the stepper controller. 

1. Power up machine
2. Command base steppers in velocity  mode
3. Command base steppers in position  mode

The position mode command can cause sudden motion of the base as its controller is not correctly initialized. This is a firmware bug.  

To replicate the bug:

1. Place the base on a thick book or other object to get the wheels off the ground
2. Power up machine from off state
3. Run code below

```python
import stretch_body.robot
from time import sleep

robot = stretch_body.robot.Robot()
robot.startup()

robot.base.set_translate_velocity(0)
robot.push_command()

robot.base.translate_by(0.1) #Causes the base to lurch forward
robot.push_command()
```

### Affected Robots

This bug affects firmware version `Stepper.v0.0.1p0`. To check your firmware version (of the arm for example), run the following and hit enter to print the actuator status:

```bash
>>$ RE1_stepper_jog.py hello-motor-arm
..
Firmware version: Stepper.v0.0.1p0
```

### Fix

To fix the bug, the stepper firmware must be updated to version `Stepper.v0.0.2p0` or later. **Note: Do not attempt to perform a firmware upgrade without contacting Hello Robot first.** You will need to:

* [Pull down the latest version](https://forum.hello-robot.com/t/updating-to-the-newest-software/303#updating-other-stretch-packages-6) of Stretch Factory from PyPi
* Follow the firmware updater instructions provided [here](https://github.com/hello-robot/stretch_firmware/blob/master/tutorials/docs/updating_firmware.md).

### Verify

To verify that the fix, try the test code again

```python
import stretch_body.robot
from time import sleep

robot = stretch_body.robot.Robot()
robot.startup()

robot.base.set_translate_velocity(0)
robot.push_command()

robot.base.translate_by(0.1) #Causes smooth motion forward
robot.push_command()
```



