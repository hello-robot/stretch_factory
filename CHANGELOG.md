# Changelog

The changes between releases of Stretch Factory is documented here.

## [0.3.0](https://github.com/hello-robot/stretch_factory/pull/52) - September 1, 2022
This release moves Stretch Factory to use a new naming scheme for its tools. The prefix `REx` is now used instead of `RE1`. This semantic change is in anticipation of the release of future versions of Stretch (e.g. RE2).

In addition, two new tools are introduced:

* REx_calibrate_guarded_contact.py: Measure the efforts required to move througout the joint workspace and save contact thresholds to Configuration YAML
* REx_calibrate_range.py: Measure the range of motion of a joint and save to the Configuration YAML.

These new tools move the the `effort_pct` contact model as supported by Stretch Body 0.3

Additional features;

* [Firmware updater tested and supports 20.04 #47](https://github.com/hello-robot/stretch_factory/pull/47)



## [0.2.0](https://github.com/hello-robot/stretch_factory/pull/45) - June 21, 2022
* [Support new parameter manage scheme #45](https://github.com/hello-robot/stretch_factory/pull/45)


Adds new parameter management format. This change will require older systems to migrate their parameters to the new format. For systems that haven't yet migrated, Stretch Body will exit with a warning that they must migrate first by running `RE1_migrate_params.py`. See the [forum post](https://forum.hello-robot.com/t/425) for more details.

## 0.1.0

* Introduce the RE1_firmware_update.py tool

## [0.0.2](https://github.com/hello-robot/stretch_factory/commit/9c44862c8f8cbaee534a603b1a22acfd042cefca) - May 13, 2020
This is the initial release of Stretch Factory. It includes tools to support debug and testing of the Stretch Hardware.

