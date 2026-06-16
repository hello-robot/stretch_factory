#!/usr/bin/env python3

import os
import stat
import argparse
import pathlib

parser = argparse.ArgumentParser(
    description="Wrap ROS2 package executables so they run within a Python virtual environment.\n"
                "Examples:\n"
                "  REx_amend_venv_execs.py stretch_funmap\n"
                "  REx_amend_venv_execs.py stretch_funmap --force\n"
                "  REx_amend_venv_execs.py stretch_demos --venv-package stretch_funmap\n"
                "  REx_amend_venv_execs.py stretch_demos --venv-package stretch_funmap --force"
)
parser.add_argument(
    "package",
    help="Package whose installed executables should be wrapped, e.g. stretch_demos"
)
parser.add_argument(
    "--venv-package",
    default=None,
    help="Package that contains the .venv to use. Defaults to the package being wrapped."
)
parser.add_argument(
    "--force",
    action="store_true",
    help="Re-wrap executables by replacing existing __ wrappers."
)
args = parser.parse_args()

ws = pathlib.Path('~/ament_ws').expanduser()
assert ws.is_dir(), f"Workspace not found: {ws}"
venv_package = args.venv_package or args.package
venv_dir = ws / 'src' / 'stretch_ros2' / venv_package / '.venv'
assert venv_dir.is_dir(), f"Virtualenv not found: {venv_dir}"

interpreter = venv_dir / 'bin' / 'python'
assert interpreter.is_file(), f"Python interpreter not found: {interpreter}"

exec_dir = ws / 'install' / args.package / 'lib' / args.package
assert exec_dir.is_dir(), f"Executable directory not found: {exec_dir}"

execs = [x for x in exec_dir.iterdir() if x.is_file()]
for e in execs:
    if e.name.startswith('__'):
        continue # don't wrap the wrapper
    new_e = e.parent / f"__{e.name}"
    if new_e.exists():
        if args.force:
            new_e.unlink()
        else:
            print(f"Skipping {e.name}: already wrapped")
            continue

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
    print(f"Wrapped {args.package}/{e.name} using {venv_package}/.venv")

