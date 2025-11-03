# CaniPy

**Serial SDARS receiver control in Python**

<img width="383" height="104" alt="CaniPy GUI" src="https://github.com/user-attachments/assets/f28d4da7-18f9-4fe9-bf3a-c04387398c6b" />

CaniPy provides a modern foundation for hobbyists to continue using supported SDARS hardware, taking advantage of Python's more legible syntax so others can better adapt this code for their needs and understand the control commands of the supported hardware.

The project can either be used by itself, currently a prototype GUI for both regular use and as a subsystem sample, or as a module that can be imported to support other scripts.

## Requirements

Python 3.10 or higher is required to run the codebase, along with the [pySerial](https://pypi.org/project/pyserial/) extension.

The current implementation supports the commands used by the following list of devices, which receive the **XM service** by Sirius XM Radio LLC.

Further support for other devices may be implemented in the future.

| Device                                       | Baud Rate |
|:---------------------------------------------|----------:|
| [PCR](https://en.wikipedia.org/wiki/XM_PCR)  |      9600 |
| Direct                                       |      9600 |
| Commander                                    |      9600 |
| [WxWorx](https://www.wxworx.com/) (Portable) |     38400 |
| WxWorx (Certified)                           |    115200 |

## Setup

The program can either be run standalone via the main script (`python3 main.py`), using [the latest pre-packaged executable from the releases page](https://github.com/canisat/canipy/releases), or by making a packaged executable in the target system.

> [!NOTE]
> Pre-packaged executable downloads already work on their own and thus do not need additional setup other than fulfilling the minimum operating system requirements for the 3.10 version of Python.

### Windows

You can identify which COM port corresponds to the radio's serial controller through Device Manager.

> [!IMPORTANT]
> The EXE may get flagged due to its use of PyInstaller for packaging to a single EXE. This is a false positive. You may alternatively download the source and run the main script instead of using the EXE.

### Linux

Your serial port device path should be designated as `/dev/ttyUSB*` or `/dev/ttyS*`.

### Mac

Your serial port device path should be designated as `/dev/cu.usbserial*` or `/dev/tty.usbserial*`.

## Usage

1. Connect the tuner to the computer.
2. Open the main program to start the CaniPy GUI.
3. Verify the device's COM/TTY port path. If the device is using a different port, change it first in the top-left input box.
4. Select the corresponding device from the drop-down menu and power it on.
5. Change channels if needed by entering the channel number on the channel input field and clicking the button underneath.
6. Power off when done.

## Packaging

After cloning the repo (`git clone //link/to/canisat.git`), if making a packaged CaniPy executable, [PyInstaller](https://pypi.org/project/pyinstaller/) must also be installed.

All necessary prerequisites will be installed automatically via `pip` when using either `make all` or `make deps`. They can alternatively be installed manually following the `requirements.txt` list.

```sh
# Recommended (deps, build)
make all  # Linux, Mac
.\build.ps1 -Task all  # Windows


# Package only
make
.\build.ps1

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

To use CaniPy as an extension for your own project, if using Git for version tracking, it is possible to add this as a submodule (`git submodule add //link/to/canisat.git`). Otherwise, simply clone this repo and add the root contents to a `canipy` directory located in your own repo.

Once CaniPy is added to a project, import it to the script using `from canipy import CaniPy` and start a `CaniPy()` instance.

## Notice

This codebase is derived from [PyXM](https://github.com/timcanham/PyXM) by Timothy Canham, under the Apache 2.0 license.

Serial commands were documented from both current CaniSat research and prior work conducted by [Nick Sayer](https://sourceforge.net/u/nsayer/profile/), the linuXMPCR and Perl XM PCR projects, Hybrid Mobile Technologies, and the defunct XM Fan forums.

CaniSat, a non-profit initiative, and its incubator [NetOtt Solutions, LLC](https://netott.com/) are not affiliated with either Sirius XM Holdings Inc., Sirius XM Radio LLC, or any of its products, partners, or subsidiaries. Sirius, XM, SiriusXM and all related indicia are trademarks of Sirius XM Holdings Inc.

The data products distributed in the service(s) are intended to be supplemental and advisory per the provider. It is not recommended for use in circumstances that require immediate urgency to fulfill safety-critical work. Both CaniSat and the service provider are not responsible for errors and inaccuracies encountered when utilizing the service data products.

CaniSat does not condone or encourage the use of its affiliated projects for unauthorized copying, duplication, or distribution of copyrighted materials received through the supported services. The end user is solely responsible for ensuring their activities comply with applicable copyright laws and service terms. Don't steal music.
