import setuptools
from os import listdir
from os.path import isfile, join


with open("README.md", "r") as fh:
    long_description = fh.read()

script_path='./bin'
stretch_scripts={script_path+'/'+f for f in listdir(script_path) if isfile(join(script_path, f))}

setuptools.setup(
    name="hello_robot_stretch_factory",
    version="0.0.9",
    author="Hello Robot Inc.",
    author_email="support@hello-robot.com",
    description="Stretch Factory Tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hello-robot/stretch_factory",
    scripts = stretch_scripts,
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ],
    install_requires=['numpy', 'scipy', 'matplotlib', 'ipython', 'jupyter', 'pandas', 'sympy', 'nose', 'PyYaml',
                      'inputs', 'drawnow', 'rplidar', 'snakeviz', 'pyusb', 'SpeechRecognition', 'pixel-ring',
                      'click', 'cma', 'opencv-contrib-python', 'colorama', 'llvmlite==0.31.0', 'numba',
                      'scikit-image', 'open3d', 'pyrealsense2', 'hello-robot-stretch-body']
)