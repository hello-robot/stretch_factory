# 011_HEAD_TILT_SWAP

### **Background**

After installing a new head tilt module the URDF calibration needs to be updated. In addition, we will want to store a local copy of the D435i calibration data.

### Test Head

First check that the new head hardware is working correctly. Jog the head around using the command line tool:

```bash
>>$  stretch_head_jog.py 
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
-------------------

```

Next check that the D435i Camera can generate point clouds:

```bash
>>$ realsense-viewer
```

### Update D435i Calibration Data 

First, pull down the files

```bash
>>$ cd ~/repos
>>$ git clone https://github.com/hello-robot/stretch_factory
```

Now copy them over

```bash
>>$ cd ~/repos/stretch_factory/updates/011_WRIST_SWAP
>>$ sudo cp * ~/stretch_user/stretch-re1-1007/calibration_D435i
>>$ sudo cp * /etc/hello-robot/stretch-re1-1007/calibration_D435i
```

### Update URDF Calibration

The URDF will need re-calibration given the new head hardware. The calibration procedure is described in detail [here](https://github.com/hello-robot/stretch_ros/tree/master/stretch_calibration#calibrate-the-stretch-re1). 



You're all set!