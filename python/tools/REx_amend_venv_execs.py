#!/usr/bin/env python3

import os
import stat
import argparse
import pathlib

parser = argparse.ArgumentParser(
    description="Tool to wrap executables to ensure they run within a Python virtual environment.\n"
                "Only supports Stretch Funmap currently.\n"
                "Example Usage:\n"
                "REx_amend_venv_execs.py stretch_funmap"
)
parser.add_argument("package")
args = parser.parse_args()

ws = pathlib.Path('~/ament_ws').expanduser()
assert ws.is_dir()
venv_dir = ws / 'src' / 'stretch_ros2' / args.package / '.venv'
assert venv_dir.is_dir()
interpreter = venv_dir / 'bin' / 'python'
assert interpreter.is_file()
exec_dir = ws / 'install' / args.package / 'lib' / args.package
assert exec_dir.is_dir()
execs = [x for x in exec_dir.iterdir() if x.is_file()]
for e in execs:
    if e.name.startswith('__'):
        continue # don't wrap the wrapper
    new_e = e.parent / f"__{e.name}"
    if new_e.exists():
        continue # this exec has already been wrapped
    e.rename(new_e)
    e.write_text(f"""#!/usr/bin/python3
import os
import sys
import subprocess
if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    bin_path = os.path.join(dir_path, '{new_e.name}')
    vpy_path = "{interpreter}"
    cmd = vpy_path + ' ' + bin_path
    if len(sys.argv) > 1:
        cmd += ' ' + ' '.join(sys.argv[1:])
    sys.exit(subprocess.call(cmd, shell=True))
"""
    )
    e.chmod(e.stat().st_mode | stat.S_IEXEC)
    print(f"Wrapped {e.name}")

