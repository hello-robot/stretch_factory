# 002_HEAD_PAN

### **Background**

Early Stretch robots have a production issue where the range of motion of the head pan is unnecessarily restricted. This is due to:

* The Dynamixel servo encoder has a range of 0-4096 ticks which corresponds to a 360 degree range of motion. As configured, the servo can not move past the 4096 tick 'rollover point'. Proper installation of the head pan gear train ensures that this rollover point is outside of the normal range-of-motion of the head.
* In some early units, this rollover point is inside the normal range-of-motion. As a result, the head pan range is limited. In this case, the robot can look all the way to its left, but can not look to its right past approximately 180 degrees --whereas it should be able to look to its right 234 degrees.

For reference, the nominal range of motion for the head is described [here](https://docs.hello-robot.com/hardware_user_guide/#head).

### Impact

The performance is degraded in autonomous actions that require a large range of motion. In particular, when [mapping an environment with FUNMAP](https://github.com/hello-robot/stretch_ros/blob/master/stretch_funmap/README.md). Tasks that don't require a large range of motion (such as human-robot interaction) are not impacted.

### Upgrade

The fix requires 3 steps:

* Mechanically reinstall the head pan gear so that the servo rollover point lands in the correct spot
* Update the YAML so that the head pan zero is still looking straight ahead
* Recalibrate the URDF to ensure a slight alignment error has not been introduced

