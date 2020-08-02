# 003_GUTHRIE_UPDATES

### **Background**

This update performs a number of minor installations to upgrade functionality on earlier robots in the 'Guthrie' batch. These updates are:

* Update to latest versions of `stretch_body` and `stretch_ros`
* Install media assets to support the new `stretch_about.py` tool
* Update librealsense URDF description packages
* Install packages to support the new `stretch_respeaker_jog.py` tool

### Impact

These updates don't change the existing robot functionality. They make available the new tools mentioned above. 

### Upgrade

First, install the necessary repos:

```bash
>>$ cd ~/repos
>>$ git clone https://github.com/hello-robot/stretch_factory
>>$ git clone https://github.com/hello-robot/stretch_install
```

, or if the repos are already present:

```bash
>>$ cd ~/repos/stretch_factory
>>$ git update
>>$ cd ~/repos/stretch_install
>>$ git update
```

Then run the update script

```bash
>>$ cd ~/repos/stretch_factory/updates/003_GUTHRIE_UPDATES
>>$ ./003_install_updates.sh
```

