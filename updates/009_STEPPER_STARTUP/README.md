

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

### Fix

To fix the bug the stepper firmware must be updated. The instructions to update firmware are provided [here](https://github.com/hello-robot/stretch_firmware). You will need to:

* Pull down the latest version of stretch_firmware from Git
* Install the Arduino command line tools if not present
* Follow the section on [Update the Steppers](https://github.com/hello-robot/stretch_firmware#update-the-steppers).

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



