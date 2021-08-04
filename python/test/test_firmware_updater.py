import unittest
from stretch_factory.firmware_updater import *


class TestFirmwareUpdater(unittest.TestCase):
    # def test_single_update(self):
    #     print('Testing Single Update')
    #     device_name='hello-motor-arm'
    #     use_device={'hello-motor-lift': False, 'hello-motor-arm': False, 'hello-motor-right-wheel': False, 'hello-motor-left-wheel': False, 'hello-pimu': False, 'hello-wacc':False}
    #     use_device[device_name]=True
    #     c = CurrrentConfiguration(use_device)
    #     r = FirmwareRepo()
    #     u = FirmwareUpdater(use_device, c, r)
    #     self.assertTrue(u.startup())
    #     v_start=FirmwareVersion(c.config_info[device_name]['board_info']['firmware_version'])
    #     available=r.versions[device_name]
    #     self.assertTrue(len(available)>=2) #Need at least two tagged version for the installed protocol of Stretch Body for this to work
    #     #Update to all availble versions
    #     for v_test in available:
    #         if v_test!=v_start:
    #             u.target[device_name]=v_test
    #             self.assertTrue(u.do_update(no_prompts=True))
    #     u.target[device_name]=v_start
    #     self.assertTrue(u.do_update(no_prompts=True))

    def test_all_update(self):
        #This will install all available tags to each device, and then restore the original version
        print('Testing All Update')
        use_device={'hello-motor-lift': True, 'hello-motor-arm': True, 'hello-motor-right-wheel': True, 'hello-motor-left-wheel': True, 'hello-pimu': True, 'hello-wacc':True}
        c = CurrrentConfiguration(use_device)
        r = FirmwareRepo()
        u = FirmwareUpdater(use_device, c, r)
        self.assertTrue(u.startup())
        for device_name in use_device.keys():
            v_start=FirmwareVersion(c.config_info[device_name]['board_info']['firmware_version'])
            available=r.versions[device_name]
            if len(available)>=2: #Need at least two tagged version for the installed protocol of Stretch Body for this to work
                #Update to all availble versions
                for v_test in available:
                    if v_test!=v_start:
                        u.target[device_name]=v_test
                        self.assertTrue(u.do_update(no_prompts=True))
                u.target[device_name]=v_start
                self.assertTrue(u.do_update(no_prompts=True))


