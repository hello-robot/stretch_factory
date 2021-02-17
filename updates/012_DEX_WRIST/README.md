# 012_DEX_WRIST

## **Background**

This update installs and configures the Beta unit of the Dexterous Wrist. The procedure involves

1. Install Stretch software packages
2. Install the new Wacc board
3. Configure the new Wacc board
4. Attach the Dexterous Wrist
5. Update the Dynamixel servo baud rates
6. Update the robot YAML
7. Test the wrist with the XBox controller

![](./images/dex_wrist_A.png)

## Install Stretch Software Packages

You'll be installing a beta version of relevant Stretch packages

```bash
>>$ cd ~/repos
>>$ mkdir beta
>>$ cd beta
>>$ git clone --branch dexterous_wrist https://github.com/hello-robot/stretch_body
>>$ git clone --branch dex_wrist https://github.com/hello-robot/stretch_factory
>>$ cd stretch_body/body
>>$ ./local_install.sh
>>$ cd ../tools
>>$ ./local_install.sh
>>$ cd ../../stretch_factory/python/
>>$ ./local_install.sh
```

## Install the new Wacc board

## Configure the Wacc board

```bash
>>$ cd ~/repos/stretch_factory/updates/012_DEX_WRIST
>>$ sudo cp *.rules /etc/udev/rules.d
>>$ sudo cp *.rules /etc/hello-robot/$HELLO_FLEET_ID/udev
```

Now power down the robot.  Power it back oncheck that the new wrist shows up on the bus

```bash
>>$ ls /dev/hello-dynamixel-wrist
>>$ ls /dev/hello-wacc
```

Then check that the Wacc is reporting sensor data back:

```bash
>>$  stretch_wacc_jog.py 
For use with S T R E T C H (TM) RESEARCH EDITION from Hello Robot Inc.

------ MENU -------
m: menu
r: reset board
a: set D2 on
b: set D2 off
c: set D3 on
d: set D3 off
-------------------

------------------------------
Ax (m/s^2) 9.8684213638
Ay (m/s^2) 0.506848096848
Az (m/s^2) 0.361166000366
A0 381
D0 (In) 1
D1 (In) 1
D2 (Out) 0
D3 (Out) 0
Single Tap Count 25
State  0
Debug 0
Timestamp 1601320914.65
Board version: Wacc.Guthrie.V1
Firmware version: Wacc.v0.0.1p0
------ MENU -------
m: menu
r: reset board
a: set D2 on
b: set D2 off
c: set D3 on
d: set D3 off
-------------------

```

Finally, jog the wrist yaw joint:

```bash
>>$ stretch_wrist_yaw_home.py 
For use with S T R E T C H (TM) RESEARCH EDITION from Hello Robot Inc.

Moving to first hardstop...
Contact at position: -3029
Hit first hardstop, marking to zero ticks
Raw position: 14
Moving to calibrated zero: (rad)

```

### Update Wacc Calibration

```bash
>>$ RE1_wacc_calibrate.py
RE1_wacc_calibrate.py 
Calibrating Wacc. Ensure arm is retracted and level to ground
Hit enter when ready

Itr 0 Val 9.59977857901
...
Itr 99 Val 10.1095601333
Got a average value of 10.1372113882
Gravity scalar of 0.967391 within bounds of 0.900000 to 1.100000
Writing yaml...

```

## Attach the Dexterous Wrist

First, remove the standard Stretch Gripper [according to the Hardware User Guide](https://docs.hello-robot.com/hardware_user_guide/#gripper-removal). 

Next, note where the forward direction is on the wrist yaw tool plate. The forward direction is indicated by the  additional alignment hole that is just outside the bolt pattern (shown pointing down in the image)

![](./images/dex_wrist_C.png)

Next, using a Philips screwdriver, attache the wrist mount bracket to the bottom of the tool plate using the provided  M2 bolts. 

**NOTE: ensure that the forward direction of the bracket (also indicated by an alignment hole) matches the forward direction of the tool plate.**



![![]](./images/dex_wrist_B.png)

Next, raise the wrist module up vertically into the mounting bracket, then sliding it over horizontally so that the bearing mates onto its post. Slide in the 3D printed spacer between the pitch servo and the mounting bracket.

![![]](./images/dex_wrist_D.png)

![![]](./images/dex_wrist_F.png)

Finally, attach the body of the pitch servo to the mounting bracket using the 3 M2.5 screws provided.

![](./images/dex_wrist_E.png)

## Update the Dynamixel servo baud rates

First, check that the servos appear on the bus:

```bash
>>$ RE1_dynamixel_id_scan.py /dev/hello-dynamixel-wrist --baud 115200
Scanning bus /dev/hello-dynamixel-wrist at baud rate 115200
----------------------------------------------------------
...
[Dynamixel ID:014] ping Succeeded. Dynamixel model number : 1060
[Dynamixel ID:015] ping Succeeded. Dynamixel model number : 1120
[Dynamixel ID:016] ping Succeeded. Dynamixel model number : 1020
...

>>$ RE1_dynamixel_id_scan.py /dev/hello-dynamixel-wrist --baud 57600
Scanning bus /dev/hello-dynamixel-wrist at baud rate 57600
----------------------------------------------------------
...
[Dynamixel ID:013] ping Succeeded. Dynamixel model number : 1060
...
```

The new wrist requires moving to 115200 Baud communication with the Stretch Dynamixel servos from the previous 57600.

```bash
>>$ RE1_dynamixel_set_baud.py /dev/hello-dynamixel-head 11 115200
---------------------
Checking servo current baud for 57600
----
Identified current baud of 57600. Changing baud to 115200
Success at changing baud

>>$ RE1_dynamixel_set_baud.py /dev/hello-dynamixel-head 12 115200
---------------------
Checking servo current baud for 57600
----
Identified current baud of 57600. Changing baud to 115200
Success at changing baud

>>$ RE1_dynamixel_set_baud.py /dev/hello-dynamixel-wrist 13 115200
---------------------
Checking servo current baud for 57600
----
Identified current baud of 57600. Changing baud to 115200
Success at changing baud
```



## Update the robot YAML

The new wrist requires a number of updates to the robot YAML.  

```bash
>>$ cd ~/repos/stretch_factory/updates/012_DEX_WRIST
>>$ cat stretch_re1_tool_params.yaml >> ~/stretch_user/$HELLO_FLEET_ID/stretch_re1_tool_params.yaml
>>$ cat stretch_re1_user_params.yaml >> ~/stretch_user/$HELLO_FLEET_ID/stretch_re1_user_params.yaml
```

YAML doesn't allow definition of multiple fields with the same name. Depending on what is already listed in your YAML you may need to manually edit and merge fields. For example:

```yaml
#Original YAML
end_of_arm:
  devices:
    stretch_gripper:
      py_class_name: StretchGripper
      py_module_name: stretch_body.stretch_gripper

# New YAML
end_of_arm:
  use_group_sync_read: 1
  retry_on_comm_failure: 1
  baud: 115200
  devices:
    wrist_pitch:
      py_class_name: WristPitch
      py_module_name: stretch_body.wrist_pitch
    wrist_roll:
      py_class_name: WristRoll
      py_module_name: stretch_body.wrist_roll
```

Becomes:

```yaml
# New YAML
end_of_arm:
  use_group_sync_read: 1
  retry_on_comm_failure: 1
  baud: 115200
  devices:
    wrist_pitch:
      py_class_name: WristPitch
      py_module_name: stretch_body.wrist_pitch
    wrist_roll:
      py_class_name: WristRoll
      py_module_name: stretch_body.wrist_roll
    stretch_gripper:
      py_class_name: StretchGripper
      py_module_name: stretch_body.stretch_gripper
```

Each user account on Stretch will need to update their YAML as well. It is recommended practice to stored a reference of the YAML in /etc so that it will be available to other (new) user  accounts.

```bash
>>$ cd ~/stretch_user/$HELLO_FLEET_ID
>>$ sudo cp *.yaml /etc/hello-robot/$HELLO_FLEET_ID
```

## Test the wrist with the XBox Controller

Try out the new wrist! Note that the new key mapping does not allow for control of the head. 

![](./images/stretch_re1_dex_wrist_teleop_guide.png)

```bash
>>$ stretch_xbox_controller_teleop.py --dex_wrist
```

A printable copy of the teleoperation interface is [here](stretch_re1_dex_wrist_teleop_guide.pdf)