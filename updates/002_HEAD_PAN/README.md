# 002_HEAD_PAN

### **Background**

Early Stretch robots have a production issue where the range of motion of the head pan is unnecessarily restricted. This is due to:

* The Dynamixel servo encoder has a range of 0-4096 ticks which corresponds to a 360 degree range of motion. As configured, the servo can not move past the 4096 tick 'rollover point'. Proper installation of the head pan gear train ensures that this rollover point is outside of the normal range-of-motion of the head.
* In some early units, this rollover point is inside the normal range-of-motion. As a result, the head pan range is limited. In this case, the robot can look all the way to its left, but can not look to its right past approximately 180 degrees --whereas it should be able to look to its right 234 degrees.

For reference, the nominal range of motion for the head is described [here](https://docs.hello-robot.com/hardware_user_guide/#head).

### Impact

The performance is degraded in autonomous actions that require a large range of motion. In particular, when [mapping an environment with FUNMAP](https://github.com/hello-robot/stretch_ros/blob/master/stretch_funmap/README.md). Tasks that don't require a large range of motion (such as human-robot interaction) are not impacted.

### Upgrade

**Mechanical Update**

First, you will need to reinstall the head pan gear so that the servo rollover point lands in the correct spot. You should have received a tool kit from Hello Robot to help you with the procedure. This will take approximately 30 minutes by someone who is mechanically inclined. Please email support@hello-robot.com if you're unsure about the procedure.

* [Video instructions](https://www.youtube.com/watch?v=6YUdjHJ_Pi4&feature=youtu.be)
* [Written instructions](./head_pan_update.pdf)

**YAML Update**

Next, you will want to update your YAML so that the head pan zero is still looking straight ahead.

```bash
>>$ cd $HELLO_FLEET_PATH/$HELLO_FLEET_ID
```

 Open `stretch_re1_factory_params.yaml` in an editor and find the `head_pan` section. You'll see something like:

```yaml
head_pan:
  flip_encoder_polarity: 1
  gr: 1.0
  id: 11
  max_voltage_limit: 15
  min_voltage_limit: 11
  motion:
    default:
      accel: 8.0
      vel: 3.0
    fast:
      accel: 10.0
      vel: 5.0
    max:
      accel: 14
      vel: 7
    slow:
      accel: 4.0
      vel: 1.0
  pid:
  - 640
  - 0
  - 0
  pwm_limit: 885
  range_t:
  - 80
  - 3900
  req_calibration: 0
  return_delay_time: 0
  stall_max_effort: 20.0
  stall_max_time: 1.0
  stall_min_vel: 0.1
  temperature_limit: 72
  usb_name: /dev/hello-dynamixel-head
  use_multiturn: 0
  zero_t: 2048
```

Update the `zero_t` field to `1235`

```yaml
head_pan:
...
  zero_t: 1235
```

Save your work. You'll also want to update the backup of this file on your machine:

```bash
>>$ sudo cp $HELLO_FLEET_PATH/$HELLO_FLEET_ID/stretch_re1_factory_params.yaml /etc/hello-robot/$HELLO_FLEET_ID
```

**Quick Test**

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
1: speed slow
2: speed default
3: speed fast
4: speed max

```

 Verify that it looks straight ahead and looks straight back as expected when commanded from the tool's menu.

**Calibration Update**

Finally, you may want to recalibrate the URDF to ensure a slight alignment error has not been introduced. This is a slightly more involved process and can take around an hour. The process [is described here](https://github.com/hello-robot/stretch_ros/blob/master/stretch_calibration/README.md).

That's it, you're all set!

