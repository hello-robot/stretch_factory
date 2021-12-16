# 017_D435I_TEST

## **Background**

This update describes a series of tests to evaluate if the Stretch D435i camera is working properly.

## Check USB version

Reboot the robot. After reboot, check that the camera is detected as USB 3.2:

```bash
>>$ rs-enumerate-devices | grep Usb
    Usb Type Descriptor           :     3.2
```

## Test data collection

Create a data collection configuration file:
```
>>$ cd 
>>$ nano data_collect.cfg
```
And add the following:

```
#Video streams
DEPTH,1280,720,15,Z16,0
INFRARED,640,480,15,Y8,1
INFRARED,640,480,15,Y8,2
COLOR,1280,720,15,RGB8,0
# IMU streams will produce data in m/sec^2 & rad/sec
ACCEL,1,1,63,MOTION_XYZ32F
GYRO,1,1,200,MOTION_XYZ32F
```

Next clear the system log
``` sudo dmesg -c```

And collect 1000 frames from the camera

```
rs-data-collect -c ./data_collect.cfg -f ./log.csv -t 60 -m 1000
```

