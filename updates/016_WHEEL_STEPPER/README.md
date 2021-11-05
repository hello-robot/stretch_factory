# 016_WHEEL_STEPPER

## **Background**

This update configures the robot (stretch-re1-xxxx) to use a new wheel module.

## Clone the repo

First, configure the software:

```bash
>>$ cd ~/repos
>>$ git clone https://github.com/hello-robot/stretch_factory
>>$ cd stretch_factory/updates/016_WHEEL_STEPPER
>>$ ./configure_new_stepper.py
```

## Test the Motor

First power down the robot. Power the robot back on and check that the board is on the bus:

```bash
>>$ ls /dev/hello-motor-*wheel
/dev/hello-motor-left-wheel  /dev/hello-motor-right-wheel
```

Finally, check that the base moves correctly. Use the `f` and `b` commands to jog the base forward and back.

```bash
stretch_base_jog.py 
For use with S T R E T C H (TM) RESEARCH EDITION from Hello Robot Inc.

--------------
m: menu

1: rate slow
2: rate default
3: rate fast
4: rate max
w: CW/CCW 90 deg
x: forward-> back 0.5m
y: spin at 22.5deg/s

f / b / l / r : small forward / back / left / right
F / B / L / R : large forward / back / left / right
o: freewheel
p: pretty print
q: quit

Input?
```
