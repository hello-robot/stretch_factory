# 006_DXL_RUNSTOP

### **Background**

For robots with serial number prior to `stretch-re1-1023` the Dynamixel servos do not respond to the runstop button. While the robot's hardware architecture prevents integrating the runstop with the Robotis servos, we have implemented a software update that simulates this behavior. This update ships with robots starting with `stretch-re1-1023`.

Note: This runstop behavior is only effective when there is an instance of the [Robot](https://github.com/hello-robot/stretch_body/blob/dxl_runstop/body/stretch_body/robot.py) class running. 

### Update YAML

Robots with serial numbers `stretch-re1-1001` to `stretch-re1-1022` will need to update their user YAML Add the following to `~/stretch_user/$HELLO_FLEET_ID/stretch_re1_user_params.yaml`

```
robot_sentry:
  dynamixel_stop_on_runstop: 1
```

**Note**: This fix is only applied to the current user account. If there are other existing user accounts they will want to apply this fix as well.

### Update Stretch Body

First, move to the latest Stretch Body package (version >=0.0.19)

```
>>$ pip2 install hello-robot-stretch-body
```

Now test it out. Try running the Xbox controller and verify that the robot head, wrist, and gripper stop their motion when the runstop is hit.

```bash
>>$ stretch_xbox_controller_teleop.py 
```

That's it!



