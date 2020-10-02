# 002_HEAD_PAN

### **Background**

Early Stretch robots have a production issue where the range of motion of the head pan is unnecessarily restricted. This is due to:

* The Dynamixel servo encoder has a range of 0-4096 ticks which corresponds to a 360 degree range of motion. As configured, the servo can not move past the 4096 tick 'rollover point'. Proper installation of the head pan gear train ensures that this rollover point is outside of the normal range-of-motion of the head.
* In some early units, this rollover point is inside the normal range-of-motion. As a result, the head pan range is limited. In this case, the robot can look all the way to its left, but can not look to its right past approximately 180 degrees --whereas it should be able to look to its right 234 degrees.

For reference, the nominal range of motion for the head is described [here](https://docs.hello-robot.com/hardware_user_guide/#head).

### Impact

* The performance is degraded in autonomous actions that require a large range of motion. In particular, when [mapping an environment with FUNMAP](https://github.com/hello-robot/stretch_ros/blob/master/stretch_funmap/README.md). 
* The servo may not respect the hardstop of the joint. This can cause it go into an error state due to overload of the servo as it pushes into the hardstop.

### Fix

We will enable hardstop based homing of the head pan. This allows the Dynamixel servo to use Multiturn Mode (and avoid the encoder rollover issue).

First, move to the latest Stretch Body package (version >=0.0.17) and the lastest Stretch Body Tools package (version >=0.0.13)

```
>>$ pip2 install hello-robot-stretch-body
>>$ pip2 install hello-robot-stretch-body-tools
```

Now update the user YAML to enable homing of the head pan joint. Add the following to `~/stretch_user/$HELLO_FLEET_ID/stretch_re1_user_params.yaml`

```
head_pan: #Fix for gear offset
  range_t:
  - 0
  - 3820
  req_calibration: 1
  use_multiturn: 1
  zero_t: 1155
  pwm_homing:
    - -300
    - 300
```

**Note**: This fix is only applied to the current user account. If there are other existing user accounts they will want to apply this fix as well.

Next, add this same bit of YAML to the factory image version of the file. This will ensure that when new user accounts are made the fix is applied. This file can be found at `/etc/hello-robot/$HELLO_FLEET_ID/stretch_re1_user_params.yaml`


### **Quick Test**

Check that your head is back up and running correctly. Run `stretch_head_jog.py`

```bash
>>$ stretch_head_jog.py 
For use with S T R E T C H (TM) RESEARCH EDITION from Hello Robot Inc.

------ MENU -------
m: menu
a: increment pan 10 deg
b: decrement pan 10 deg
c: increment tilt 10 deg
d: decrement tilt 10 deg
e: ahead
f: back
g: tool
h: wheels
i: left
j: up
p: pan go to pos ticks
t: tilt go to pos ticks
x: home
1: speed slow
2: speed default
3: speed fast
4: speed max

```
Try out the homing with the 'x' command.  Verify that it looks straight ahead ('e') and looks straight back ('f') as expected when commanded from the tool's menu.

**URDF Calibration **

Finally, you will want to recalibrate the URDF. This is a slightly more involved process and can take around an hour. The process [is described here](https://github.com/hello-robot/stretch_ros/blob/master/stretch_calibration/README.md).

That's it, you're all set!

