#!/usr/bin/env python
import stretch_body.arm as arm

# ######## Modify These ###############
def calibrate_range():
        a=arm.Arm()
        a.startup()
        extension_m=a.home(single_stop=False,measuring=True)
        if extension_m is not None:
            print 'Measured an arm extension of ',extension_m
            print 'Save to factory settings [n]?'
            x=raw_input()
            if x=='y' or x=='Y':
                a.params['range_m'][1]=extension_m
                a.write_device_params('arm',a.params)
                return ['Wrote arm range calibration to YAML',1]
        return ['Arm range calibration fail', 0]

if __name__ == "__main__":
    calibrate_range()