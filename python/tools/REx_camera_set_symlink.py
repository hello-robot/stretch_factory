import stretch_body.hello_utils as hu
import argparse
import sys
import os
from stretch_factory import hello_device_utils as hdu
from datetime import datetime

hu.print_stretch_re_use()


parser = argparse.ArgumentParser(description="Tool to assign an camera symlink to plugged-in USB camera"
                                             " by generating an UDEV rule.\n"
                                             "Example Usage:\n"
                                             "REx_camera_set_symlink.py --port /dev/video6 --symlink hello-navigation-camera"
                                             )

group = parser.add_mutually_exclusive_group(required=False)
group.add_argument('--port', type=str,help='Plugged in USB camera video device port. E.g. --port /dev/video4')
group.add_argument('--name', type=str,help="Plugged in USB camera video device's name pattern. E.g. --name Logitech")
parser.add_argument('--symlink', type=str,help='Symlink to be created E.g. --symlink hello-navigation-camera')
parser.add_argument('--list', help='List all the enumerated Video devices',action="store_true")

args = vars(parser.parse_args())

def print_video_devices_list():
    print("Found the following Video Devices:\n\n")
    video_devices = hu.get_video_devices()
    for device in video_devices:
        print(f"{device}")
        print(f"Ports: {video_devices[device]}")
        print("\n")


def reset_udev_ctrl():
    os.system("sudo udevadm control --reload; sudo udevadm trigger")

def generate_udev_rule(port,symlink):
    ID_SERIAL_SHORT = hdu.extract_udevadm_info(port,'ID_SERIAL_SHORT')
    ID_VENDOR_ID = hdu.extract_udevadm_info(port,'ID_VENDOR_ID')
    ID_MODEL_ID = hdu.extract_udevadm_info(port,'ID_MODEL_ID')
    line = f"KERNEL==\"video*\", KERNELS==\"1-1.3.*\", ATTRS{{idVendor}}==\"{ID_VENDOR_ID}\", ATTRS{{idProduct}}==\"{ID_MODEL_ID}\", MODE:=\"0777\", ATTRS{{serial}}==\"{ID_SERIAL_SHORT}\", SYMLINK+=\"{symlink}\""
    fname = f'86-{symlink}.rules'
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    with open(f"/tmp/{fname}", 'w') as file:
        # Write lines to the file
        file.write("# USB Camera Device\n\n")
        file.write("# Auto generated by REx_camera_set_symlink.py tool \n")
        file.write(f"# Date: {formatted_datetime} \n")
        file.write(line)
    os.system(f"sudo cp /tmp/{fname} /etc/udev/rules.d/")
    rules = os.listdir("/etc/udev/rules.d/")
    if fname in rules:
        print("Successfully generate udev rule at path: /etc/udev/rules.d/{fname}")
        os.system(f"sudo rm /tmp/{fname}")
        reset_udev_ctrl()
    else:
        print("Unable to generate udev rule at path: /etc/udev/rules.d/{fname}")

if args['list']:
    print_video_devices_list()
    sys.exit()
elif args['port']:
    if args['symlink']:
        print(f"Assing usb port: {args['port']} to symlink port: /dev/{args['symlink']}")
        generate_udev_rule(args['port'],args['symlink'])
    else:
        print("Symlink argument (--symlink) not provided")
elif args['name']:
    if args['symlink']:
        port = hu.get_video_device_port(args['name'])
        if port:
            print(f"Assing usb port: {port} to symlink port: /dev/{args['symlink']}")
            generate_udev_rule(port,args['set_symlink'])
        else:
            print(f"Unable to find a USB video device port matching the name: {args['name']}")
    else:
        print("Symlink argument (--symlink) not provided")
else:
    parser.print_usage()