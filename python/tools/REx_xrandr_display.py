#!/usr/bin/env python3

import stretch_body.hello_utils as hu
hu.print_stretch_re_use()

import sys
import argparse
from Xlib import display
from Xlib.ext import randr

parser = argparse.ArgumentParser(
    description="Tool to change display resolution/fps/etc.."
)
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--set', type=str, help='Set resolution to WIDTHxHEIGHTxFPS. E.g. --set 1920x1080x60.00')
group.add_argument('--set-720p', action='store_true', help='Set resolution to 1280x720xhighest_fps')
group.add_argument('--set-1080p', action='store_true', help='Set resolution to 1920x1080xhighest_fps')
group.add_argument('--revert', action='store_true', help='Revert resolution to whatever it was before --set was called. Does nothing if prev resolution not saved or cleared with reboot.')
group.add_argument('--list', action='store_true', help='List all available resolutions for the display')
group.add_argument('--current', action='store_true', help='Print out the current resolution being used')
args = vars(parser.parse_args())

def find_mode(id, modes):
    for mode in modes:
        if id == mode.id:
            return f"{mode.width}x{mode.height}x{mode.dot_clock / (mode.h_total * mode.v_total)}"

def get_display_info():
    try:
        d = display.Display(':0')
    except:
        print('Error: No display available')
        sys.exit(1)

    screen_count = d.screen_count()
    if screen_count == 0:
        print('Error: No display plugged in')
        sys.exit(1)
    elif screen_count != 1:
        print(f'Error: This tool only supports 1 display. There are {screen_count} plugged in')
        sys.exit(1)

    s = d.screen(0)
    window = s.root
    res = randr.get_screen_resources(window)
    result = []
    for output in res.outputs:
        params = d.xrandr_get_output_info(output, res.config_timestamp)
        if not params.crtc:
            continue
        crtc = d.xrandr_get_crtc_info(params.crtc, res.config_timestamp)
        crtc_resolution = f"{crtc.width}x{crtc.height}"
        crtc_mode = find_mode(crtc.mode, res.modes)
        if crtc_mode == None or crtc_resolution not in crtc_mode:
            print('Error: Unable to find resolution mode for current display')
            sys.exit(1)
        modes = set()
        for mode in params.modes:
            modes.add(find_mode(mode, res.modes))
        result.append({
            'name': params.name,
            'resolution': crtc_mode,
            'available_resolutions': list(modes),
        })

    if len(result) == 0:
        print('Error: No display plugged in')
        sys.exit(1)
    elif len(result) != 1:
        print(f'Error: This tool only supports 1 display. There are {len(result)} plugged in')
        sys.exit(1)

    return result[0]

if args['current']:
    info = get_display_info()
    print(f"Display Name:       {info['name']}")
    print(f"Display Resolution: {info['resolution']}")
elif args['list']:
    print('okay')
else:
    print('oh no')

