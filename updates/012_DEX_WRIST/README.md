# 012_DEX_WRIST

## **Background**

This update installs and configures the Beta unit of the Dexterous Wrist. The procedure involves

1. Install Stretch software packages
2. Install the new Wacc board
3. Configure the new Wacc board
4. Attach the Dexterous Wrist
5. Update the Dynamixel servo baud rates
6. Update the user YAML
7. Test the wrist with the XBox controller

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
>>$ sudo cp *.rules /etc/hello-robot/stretch-re1-1018/udev
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

Now copy the updated YAML to /etc so that it will be available to other (new) user  accounts.

```bash
>>$ cd ~/stretch_user/stretch-re1-1018
>>$ sudo cp stretch_re1_factory_params.yaml /etc/hello-robot/stretch-re1-1018
```

## Attach the Dexterous Wrist

First, remove the standard Stretch Gripper [according to the Hardware User Guide](https://docs.hello-robot.com/hardware_user_guide/#gripper-removal). 

