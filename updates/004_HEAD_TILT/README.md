# 004_HEAD_TILT

### **Background**

Tools to debug the head tilt unit not working (assuming not a mechanical failure or unplugged cable)



Check that both the pan and tilt are on the bus

```bash
>>$ RE1_dynamixel_scan.py /dev/hello-dynamixel-head
```



Reboot the servos of the head

```bash
>>$ RE1_dynamixel_reboot.py /dev/hello-dynamixel-head
```



Directly jog the tilt joint (ID 12) from the menu

```bash
>>$ RE1_dynamixel_jog.py /dev/hello-dynamixel-head 12
```



Jog the entire head

```bash
>>$ stretch_head_jog.py
```

