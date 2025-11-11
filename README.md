# CaniPy

**Serial SDARS receiver control in Python**

<img width="320" height="240" alt="CaniPy GUI" src="https://github.com/user-attachments/assets/0bd820bd-90e3-447e-9f33-3bdddafba0bd" />

CaniPy provides a modern foundation for hobbyists to continue using supported satellite radio hardware.

The project can either be used by itself with a GUI or as a module that can be imported to support other scripts.

Taking advantage of Python's more legible syntax, other projects can adapt this code for their needs and understand the control commands of the supported hardware.

## Requirements

The following are required to run CaniPy:

* A system that meets the minimum requirements for **Python 3.10**
    * Windows 8.1 or higher
    * macOS 10.9 or higher
    * Linux
* A compatible serial-controlled satellite radio that is listed below, which receives the **XM service** by Sirius XM Radio LLC

| Device                                       | Baud Rate |
|:---------------------------------------------|----------:|
| [PCR](https://en.wikipedia.org/wiki/XM_PCR)  |      9600 |
| Direct                                       |      9600 |
| Commander                                    |      9600 |
| [WxWorx](https://www.wxworx.com/) (Portable) |     38400 |
| WxWorx (Certified)                           |    115200 |

(Further support for other devices may be implemented in the future)

## Usage

> [!IMPORTANT]
> On Windows, the standalone EXE may get flagged due to its use of PyInstaller for packaging. This is a false positive. You may alternatively download the source code package and run the main script directly instead.

The program can be run via either [the latest pre-packaged executable from the releases page](https://github.com/canisat/canipy/releases), the main script if using the source code (`python3 main.py`), or by making a packaged executable in the target system.

1. Connect the tuner to the computer.
2. Open the main program to start the CaniPy UI.
3. Select and verify the device's COM/TTY port path from the drop-down menu. See below for guidance depending on your operating system. If the device is using a different path, you may change it by typing in the device port box.
4. Select the corresponding device type from the drop-down menu underneath to connect and power it on.
5. Change channels if needed by first changing the number on the channel input field and then clicking the "Enter" button.
6. Assign a channel to a preset by clicking one of the 6 buttons. To clear the preset, go to "Settings" > "Clear preset" and select the button's number.
7. Mute and unmute the audio by going to "File" > "Mute".
8. Set the time zone and clock display settings in "Settings" > "Clock".
9. Close the program when done. Time display settings and presets will be stored in a configuration file.

### Windows

You can verify the COM port corresponding to the radio through the [Device Manager](https://support.microsoft.com/en-us/windows/open-device-manager-a7f2db46-faaf-24f0-8b7b-9e4a6032fc8c) and expanding the "Ports (COM & LPT)" dropdown.

### Linux

The serial port device path starts with etiher `/dev/ttyUSB*` or `/dev/ttyS*`.

### Mac

The serial port device path starts with etiher `/dev/tty.usbserial*` or `/dev/tty.*`.

## Packaging

If making a standalone CaniPy executable, first [download the released source ZIP or TAR.GZ](https://github.com/canisat/canipy/releases) or clone the repo (`git clone //link/to/canisat.git`), then install [pySerial](https://pypi.org/project/pyserial/) and [PyInstaller](https://pypi.org/project/pyinstaller/).

These prerequisites will be installed via `pip` automatically when using either `make all` or `make deps`. They can alternatively be installed manually following the `requirements.txt` list.

```sh
# Recommended (deps, build)
make all  # Linux, Mac
.\build.ps1 -Task all  # Windows


# Package only
make
.\build.ps1

# Package terminal version only
make term
.\build.ps1 -Task term

# Install req's only
make deps
.\build.ps1 -Task deps

# Clear artifacts
make clean
.\build.ps1 -Task clean


# clear, deps, build
make rebuild
.\build.ps1 -Task rebuild

# clear, build
make rebuild SKIP_DEPS=1
.\build.ps1 -Task rebuild -SkipDeps 1
```

## Module

To use CaniPy as an extension for your project, if using Git for version tracking, it is possible to add the repo as a submodule (`git submodule add //link/to/canisat.git`). Otherwise, simply clone this repo in your project root.

Once CaniPy is added to a project, import it to the script using `from canipy import CaniPy` and start a `CaniPy()` instance.

## Notice

This codebase is derived from [PyXM](https://github.com/timcanham/PyXM) by Timothy Canham, under the Apache 2.0 license.

Serial commands were documented from both current CaniSat research and prior work conducted by [Nick Sayer](https://sourceforge.net/u/nsayer/profile/), the linuXMPCR and Perl XM PCR projects, Hybrid Mobile Technologies, and the defunct XM Fan forums.

CaniSat, a non-profit initiative, and its incubator [NetOtt Solutions, LLC](https://netott.com/) are not affiliated with either Sirius XM Holdings Inc., Sirius XM Radio LLC, or any of its products, partners, or subsidiaries. Sirius, XM, SiriusXM and all related indicia are trademarks of Sirius XM Holdings Inc.

The data products distributed in the service(s) are intended to be supplemental and advisory per the provider. It is not recommended for use in circumstances that require immediate urgency to fulfill safety-critical work. Both CaniSat and the service provider are not responsible for errors and inaccuracies encountered when utilizing the service data products.

CaniSat does not condone or encourage the use of its affiliated projects for unauthorized copying, duplication, or distribution of copyrighted materials received through the supported services. The end user is solely responsible for ensuring their activities comply with applicable copyright laws and service terms. Don't steal music.
