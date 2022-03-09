# 005_HEAD_PAN_CALIBRATION

### **Background**

The URDF calibration is very sensitive to the 'zero' point of the head pan actuator. We've found that recalibration of the zero point may be necessary  on occaission -- for example if the gear teeth of the joint have skipped due to very high loading.

Starting with Stretch serial number `stretch-re1-1023` we've moved to a new method of setting the zero point. This new method allows the user to recalibrate the joint in the field.

### Update YAML

Robots with serial numbers `stretch-re1-1001` to `stretch-re1-1022` will need to update their user YAML prior to running the recalibration procedure below. Later robots do not need to update their YAML.

Add the following to `~/stretch_user/$HELLO_FLEET_ID/stretch_re1_user_params.yaml`

```
head_pan:
  range_t:
  - 0
  - 3827
  use_multiturn: 1
  zero_t: 1165
  pwm_homing:
  - -300
  - 300
```

**Note**: This fix is only applied to the current user account. If there are other existing user accounts they will want to apply this fix as well.

### Recalibration

First, move to the latest Stretch Body package (version >=0.0.17) and the latest Stretch Factory  package (version >=0.0.14)

```
>>$ pip2 install hello-robot-stretch-body
>>$ pip2 install hello-robot-stretch-factory
```

Now run the recalibration script. This will find the CCW hardstop and mark its position in the servos EEPROM.

```bash
>>$ RE1_head_calibrate_pan.py 
About to calibrate the head pan. Doing so will require you to recalibrated your URDF. Proceed (y/n)?
y
Moving to first hardstop...
Contact at position: -3
Hit first hardstop, marking to zero ticks
Raw position: 33
Moving to calibrated zero: (rad)
Recalibration done. Now redo the URDF calibration (see stretch_ros documentation)
```

### URDF Recalibration 

Finally, you will want to recalibrate the URDF. This is a slightly more involved process and can take around an hour. The process [is described here](https://github.com/hello-robot/stretch_ros/blob/master/stretch_calibration/README.md).

That's it, you're all set!

