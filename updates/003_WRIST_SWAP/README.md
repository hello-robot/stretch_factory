# 003_WRIST_SWAP

### **Background**

After installing a new wrist module the system UDEV needs to be updated

### Update UDEV 

First, pull down the files

```bash
>>$ cd ~/repos
>>$ git clone https://github.com/hello-robot/stretch_factory
```

Now copy them over

```bash
>>$ cd stretch_factory/updates/003_WRIST_SWAP
>>$ sudo cp *.rules /etc/udev/rules.d
>>$ sudo cp *.rules /etc/hello-robot/stretch-re1-1004/udev
```

Now reboot. After reboot check that the new wrist shows up on the bus

```bash
>>$ ls /dev/hello-dynamixel-wrist
>>$ ls /dev/hello-wacc
```

### Test Wrist

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
>>$ pip2 install hello-robot-stretch-factory
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

```
>>$ cd ~/stretch_user/stretch-re1-1004
>>$ sudo cp stretch_re1_factory_params.yaml /etc/hello-robot/stretch-re1-1004
```

You're all set!