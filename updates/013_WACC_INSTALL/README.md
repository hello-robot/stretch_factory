# 013_WACC_INSTALL

## **Background**

This update installs and configures a new Wacc board. You will need

- Replacement Wacc board
- USB-A to USB-micro cable



## Update the Wacc board serial numbers

First, on the robot run:

```bash
>>$ cd ~/repos
>>$ git clone https://github.com/hello-robot/stretch_factory
>>$ chmod a+rw $HELLO_FLEET_PATH/$HELLO_FLEET_ID/udev/*
```

Now attach the USB cable into a USB port of the robot. Run the updating tool. When it prompts to 'Plug / Reset'



```bash
>>$ cd stretch_factory/updates/013_WACC_INSTALL
>>$ sudo dmesg -c
>>$ ./add_new_wacc_pcba.py 
----------------------
Adding WACC PCBA to robot:  stretch-re1-1039
Plug / Reset Dynamixel device now...
Press return when done

[1035443.643968] usb 1-1.3.2.1: new high-speed USB device number 12 using xhci_hcd
[1035443.844182] usb 1-1.3.2.1: New USB device found, idVendor=1a40, idProduct=0101
[1035443.844199] usb 1-1.3.2.1: New USB device strings: Mfr=0, Product=1, SerialNumber=0
[1035443.844208] usb 1-1.3.2.1: Product: USB 2.0 Hub
[1035443.845851] hub 1-1.3.2.1:1.0: USB hub found
[1035443.845923] hub 1-1.3.2.1:1.0: 4 ports detected
[1035444.252052] usb 1-1.3.2.1.2: new full-speed USB device number 15 using xhci_hcd
[1035444.479616] usb 1-1.3.2.1.2: New USB device found, idVendor=0403, idProduct=6001
[1035444.479625] usb 1-1.3.2.1.2: New USB device strings: Mfr=1, Product=2, SerialNumber=3
[1035444.479631] usb 1-1.3.2.1.2: Product: FT232R USB UART
[1035444.479636] usb 1-1.3.2.1.2: Manufacturer: FTDI
[1035444.479640] usb 1-1.3.2.1.2: SerialNumber: AQ00X8TJ
[1035444.483900] ftdi_sio 1-1.3.2.1.2:1.0: FTDI USB Serial Device converter detected
[1035444.484043] usb 1-1.3.2.1.2: Detected FT232RL
[1035444.484466] usb 1-1.3.2.1.2: FTDI USB Serial Device converter now attached to ttyUSB3
[1035445.459995] usb 1-1.3.2.1.3: new full-speed USB device number 17 using xhci_hcd

---------------------------
Found Dynamixel device with SerialNumber AQ00X8TJ
Writing UDEV for  AQ00X8TJ
Overwriting existing entry...
Plug / Reset in Arduino device now...
Press return when done

---------------------------
Found Arduino device with SerialNumber C209885C50524653312E3120FF101E39
Writing UDEV for  hello-wacc C209885C50524653312E3120FF101E39
Overwriting existing entry...
---------------------------
Found Arduino device with SerialNumber C209885C50524653312E3120FF101E39
Writing UDEV for  hello-wacc C209885C50524653312E3120FF101E39
Overwriting existing entry...

```





## Install the new Wacc board

You will need the following tools

* 1.5mm Hex wrench
* 2.5mm Hex wrench
* Small flat head screw driver or similar
* Loctite 242 (blue)

1. Power down the robot from Ubuntu and turn off the main power switch.
2. Manually pose the lift height and arm such that the wrist can sit on a table top.
3. Using the 1.5mm wrench, remove the two M2 bolts holding the plastic cap to the end of the wrist 
4. Using the 2.5mm wrench, remove the two M4 bolts holding the wrist module to the end of arm
5. Slide the wrist module out of the arm tube while supporting the weight of the module so that it remains parallel to the ground.  Take care that the Wacc board clears the surrounding metal structure.
6. With the screw driver, push back and dislodge the JST power cable and USB cable from the Wacc board.
7. Using the 1.5mm wrench, remove the 4 M2 bolts holding the Wacc board to the sheetmetal frame. 
8. Attach the replacement board onto the sheetmetal frame, first dipping the tips of the 4 M2 bolts into a drop of Loctite
9. Reattach the USB and power cables and carefully slide the wrist module back into the arm. 
10. Secure the wrist module to the arm with the 4 M4 bolts and the plastic cap with the two M2 bolts. Apply Loctite to the bolts first.



## 



## Configure the Wacc board

```bash
>>$ cd ~/repos/stretch_factory/updates/012_DEX_WRIST
>>$ sudo cp *.rules /etc/udev/rules.d
>>$ sudo cp *.rules /etc/hello-robot/$HELLO_FLEET_ID/udev
```

Now power down the robot.  Power it back on and check that the new wrist shows up on the bus

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

Finally, home the wrist yaw joint to ensure that it is working.

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

The new wrist requires a number of updates to the robot YAML

YAML doesn't allow definition of multiple fields with the same name. Depending on what is already listed in your YAML you may need to manually edit and merge fields. 

Add the following to `~/stretch_user/$HELLO_FLEET_ID/stretch_re1_user_params.yaml`

```yaml
factory_params: stretch_re1_factory_params.yaml

params:
  - stretch_tool_share.stretch_dex_wrist_beta.params

head:
  baud: 115200

end_of_arm:
  baud: 115200
  tool: tool_stretch_dex_wrist
  #tool: tool_stretch_gripper

robot:
  use_collision_manager: 1

head_pan:
  baud: 115200

head_tilt:
  baud: 115200

wrist_yaw:
  baud: 115200

stretch_gripper:
  baud: 115200
  range_t:
    - 0
    - 6667
  zero_t: 3817

lift:
  i_feedforward: 0.75

hello-motor-lift:
  gains:
    i_safety_feedforward: 0.75


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
>>$ stretch_xbox_controller_teleop.py
```

A printable copy of the teleoperation interface is [here](stretch_re1_dex_wrist_teleop_guide.pdf)

## Configure for use in ROS

```bash
>>$ cd catkin_ws/src/stretch_ros/
>>$ git checkout feature/pluggable_end_effector
>>$ cd stretch_description

>>$ cp ~/repos/dex_wrist/stretch_tool_share/tool_share/stretch_dex_wrist_beta/stretch_description/urdf/stretch_dex_wrist_beta.xacro  urdf/
>>$ cp ~/repos/dex_wrist/stretch_tool_share/tool_share/stretch_dex_wrist_beta/stretch_description/meshes/*.STL meshes/

>>$ rosrun stretch_calibration update_urdf_after_xacro_change.sh

```

Now check that the wrist appears in RVIZ and can be controlled from the keyboard interface:

```bash
>>$ roslaunch stretch_calibration simple_test_head_calibration.launch
```



![](./images/dex_wrist_rviz.png)