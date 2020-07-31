# 001_ROS_INSTALL

### **Background**

Early Stretch units shipped without the `stretch_ros` stack installed. These scripts will install the necessary packages and bring the robot up to the current ROS compatible configuration.

### Installation

To upgrade a 'pre-ROS' Stretch to use the latest ROS software stack:

```bash
>>$ cd ~/repos
>>$ git clone https://github.com/hello-robot/stretch_factory
>>$ cd updates/STRETCH_UPDATES_001
>>$ ./stretch_install_system.sh
>>$ ./stretch_updgrade_pre_ros.sh

```

Then install your URDF to the correct place

```bash
>>$ rosrun stretch_calibration update_with_most_recent_calibration.sh
```

Now as a sanity check that everything is working, try out the [face detection demo](https://github.com/hello-robot/stretch_ros/blob/master/stretch_deep_perception/README.md).





