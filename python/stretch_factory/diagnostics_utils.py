from __future__ import print_function
from colorama import Fore, Back, Style

def val_in_range(val_name, val, vmin, vmax):
    p = val <= vmax and val >= vmin
    if p:
        print(Fore.GREEN + '[Pass] ' + val_name + ' = ' + str(val))
        return True
    else:
        print(Fore.RED + '[Fail] ' + val_name + ' = ' + str(val) + ' out of range ' + str(vmin) + ' to ' + str(vmax))
        return False


def val_is_not(val_name, val, vnot):
    if val is not vnot:
        print(Fore.GREEN + '[Pass] ' + val_name + ' = ' + str(val))
        return True
    else:
        print(Fore.RED + '[Fail] ' + val_name + ' = ' + str(val))
        return False
