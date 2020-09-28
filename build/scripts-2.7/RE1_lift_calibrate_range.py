#!python
import stretch_body.lift as lift

# ######## Modify These ###############

l=lift.Lift()
l.startup()
print 'Position lift at bottom of range. Hit enter when ready'
raw_input()
range_m=l.home(measuring=True)
if range_m is not None:
    print 'Measured a lift range of ',range_m
    print 'Save to factory settings [n]?'
    x=raw_input()
    if x=='y' or x=='Y':
        l.params['range_m'][1]=range_m
        l.write_device_params('lift',l.params)
