

# 014_WAYPOINTS

### **Background**

x

### Update Firmware

Install the latest version of the firmware for the Wacc, Pimu, and Steppers. 

NOTE: For now you will want the`sync_timestamp`branch of the git repository. You'll need to pull it down.

```bash
>>$ cd ~/repos
>>$ git clone https://github.com/hello-robot/stretch_firmware -b via_trajectory
```

Then follow [the tutorial for upgrading firmware](https://github.com/hello-robot/stretch_firmware) (Note your Stretch may already have the Arduino IDE installed and configured). 

### Update YAML

Robots with serial numbers `stretch-re1-1001` to `stretch-re1-1022` will need to update their user YAML Add the following to `~/stretch_user/$HELLO_FLEET_ID/stretch_re1_user_params.yaml`

```
pimu_clock_manager:
  n_slew_history: 25
  trs: 450.0
  use_skew_compensation: 1

wacc_clock_manager:
  n_slew_history: 25
  trs: 687.0
  use_skew_compensation: 1

robot_timestamp_manager:
  sync_mode_enabled: 1
  time_align_status: 1
```

**Note**: This fix is only applied to the current user account. If there are other existing user accounts they will want to apply this fix as well. 

### Update Stretch Body

NOTE: For now pull down the  `sync_timestamp` branch of the git repository and install that.



```bash
>>$ cd ~/repos
>>$ git clone https://github.com/hello-robot/stretch_body -b sync_timestamp
>>$ cd ~/repos/stretch_body/body
>>$ ./local_install.sh
>>$ cd ../tools
>>$ ./local_install.sh
```

FUTURE:

First, move to the latest Stretch Body package (version >=0.0.20)

```
>>$ pip2 install hello-robot-stretch-body
```

### Try It Out

Now test it out. Try running the timestamp jog tool.

```bash
>>$ stretch_robot_timestamps_jog.py --display
For use with S T R E T C H (TM) RESEARCH EDITION from Hello Robot Inc.
------ Timestamp Manager -----
Sync mode enabled    : 1
Status ID            : 121
Wall time            : 1607575532.977621
Hardware sync        : 1607575532.939872
Pimu IMU             : 1607575532.930712
Lift Encdoer         : 1607575532.938915
Arm Encoder          : 1607575532.938884
Right Wheel Encoder  : 1607575532.939187
Left Wheel Encoder   : 1607575532.938882
Wacc Accel           : 1607575532.934294
------ Timestamp Manager -----
Sync mode enabled    : 1
Status ID            : 125
Wall time            : 1607575533.187324
Hardware sync        : 1607575533.148872
Pimu IMU             : 1607575533.140704
Lift Encdoer         : 1607575533.147775
Arm Encoder          : 1607575533.148192
Right Wheel Encoder  : 1607575533.148234
Left Wheel Encoder   : 1607575533.147883
Wacc Accel           : 1607575533.142721
...


```



```bash
>>$ stretch_robot_timestamps_jog.py --sensor_delta
For use with S T R E T C H (TM) RESEARCH EDITION from Hello Robot Inc.

Starting sensor timestamp analysis...
Sync mode enabled: 1
Time align status: 0
Use skew compensation: 1
---------------------------
DT Pimu IMU            :-10152
DT Left Wheel Encoder  :-717
DT Right Wheel Encoder :-1068
DT Lift Encoder        :-361
DT Arm Encoder         :-337
DT Wacc Accel          :5703
---------------------------
DT Pimu IMU            :-7148
DT Left Wheel Encoder  :-708
DT Right Wheel Encoder :-953
DT Lift Encoder        :-470
DT Arm Encoder         :-864
DT Wacc Accel          :84

```



```
>>$ stretch_robot_timestamps_jog.py --sensor_stats
```

![](./sensor_stats.png)

That's it!



