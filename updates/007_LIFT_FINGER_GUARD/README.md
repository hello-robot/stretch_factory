# 007_LIFT_FINGER_GUARD

### **Background**

Installing the foam finger guards on the lift will require adjustment of the robot calibration. When the lift homes in the upward direction, it will now stop short of its true hardstop. To adjust for this we will pad the lift range of motion in YAML. We will then test that the URDF calibration is still in spec. If it is out of spec, we will recalibrate the URDF.

### Update YAML

Add the following to `~/stretch_user/$HELLO_FLEET_ID/stretch_re1_user_params.yaml`. This will override the default range setting, subtracting 6mm in each direction

```
lift:
  range_m:
  - 0.006
  - 1.0939
```

**Note**: This fix is only applied to the current user account. If there are other existing user accounts they will want to apply this fix as well.

### Test New Range of Motion

Home the lift and then check that the lift behaves well at the hardstops. Using the menu, jog the lift to each end of range of motion.

```bash
>>$ stretch_lift_home.py
>>$ stretch_lift_jog.py
```



### URDF Calibration

First update to the latest version of stretch_ros

```bash
>>$ cd ~/catkin_ws/src/stretch_ros
>>$ git pull
```

Now do the calibration:

```bash
>>$ stretch_robot_home.py
>>$ rosrun stretch_calibration update_uncalibrated_urdf.sh
>>$ roslaunch stretch_calibration collect_head_calibration_data.launch
```

The robot will collect calibration samples. This will take about 5 minutes. Then:

```bash
>>$ roslaunch stretch_calibration process_head_calibration_data.launch
```

This will take about an hour. Check that the reported total error at the end of calibration is low (<0.03). If the fit is good, start using the calibration. 

```bash
>>$ rosrun stretch_calibration update_with_most_recent_calibration.sh
```

And visually inspect the fit

```bash
>>$ >>$ roslaunch stretch_calibration simple_test_head_calibration.launch
```

The full URDF calibration tutorial is found [here](https://github.com/hello-robot/stretch_ros/tree/master/stretch_calibration) 

