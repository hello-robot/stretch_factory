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

Now attach the USB cable into a USB port of the robot trunk. Run the updating tool. When it prompts to 'Plug / Reset' plug in the cable to the new Wacc board (or unplug then plug back in.)

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



## Check the Wacc functionality

Power the robot back on and check that the board is on the bus

```bash
>>$ ls /dev/hello-dynamixel-wrist
hello-dynamixel-wrist
>>$ ls /dev/hello-wacc
hello-wacc
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

## Update Wacc Calibration

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

