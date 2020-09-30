# 004_HEAD_TILT

### **Background**

Tools to debug the head tilt unit not working (assuming not a mechanical failure or unplugged cable)

Check that both the pan (ID 11) and tilt (ID 12) are on the bus

```bash
>>$ RE1_dynamixel_id_scan.py /dev/hello-dynamixel-head 
[Dynamixel ID:000] ping Failed.
[Dynamixel ID:001] ping Failed.
[Dynamixel ID:002] ping Failed.
[Dynamixel ID:003] ping Failed.
[Dynamixel ID:004] ping Failed.
[Dynamixel ID:005] ping Failed.
[Dynamixel ID:006] ping Failed.
[Dynamixel ID:007] ping Failed.
[Dynamixel ID:008] ping Failed.
[Dynamixel ID:009] ping Failed.
[Dynamixel ID:010] ping Failed.
[Dynamixel ID:011] ping Succeeded. Dynamixel model number : 1060
[Dynamixel ID:012] ping Succeeded. Dynamixel model number : 1060
[Dynamixel ID:013] ping Failed.
[Dynamixel ID:014] ping Failed.
[Dynamixel ID:015] ping Failed.
[Dynamixel ID:016] ping Failed.
[Dynamixel ID:017] ping Failed.
[Dynamixel ID:018] ping Failed.
[Dynamixel ID:019] ping Failed.


```

### Things to try

Directly jog the tilt joint (ID 12) from the menu

```bash
>>$ RE1_dynamixel_jog.py /dev/hello-dynamixel-head 12
```

Directly jog the pan joint (ID 11) from the menu

```bash
>>$ RE1_dynamixel_jog.py /dev/hello-dynamixel-head 11
```

If you think a servo may have overheated, reboot the servos of the head

```bash
>>$ RE1_dynamixel_reboot.py /dev/hello-dynamixel-head
[Dynamixel ID:011] Reboot Succeeded.
[Dynamixel ID:012] Reboot Succeeded.

```

Jog the entire head. Verify the looking ahead, back, etc from the menu work as expcted

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
x: home
1: speed slow
2: speed default
3: speed fast
4: speed max
-------------------
```

