# CaniPy
### Serial SDARS receiver control in Python

<img width="383" height="104" alt="CaniPy GUI" src="https://github.com/user-attachments/assets/f28d4da7-18f9-4fe9-bf3a-c04387398c6b" />

CaniPy provides a modern foundation for hobbyists to continue using supported SDARS hardware.

The project can either be used by itself, currently a prototype GUI for both regular use and as a subsystem sample, or as a module that can be imported to support other scripts.

## Requirements
Python 3.10 or higher is required to run the codebase, along with the [pySerial](https://pypi.org/project/pyserial/) extension.

```
pip install pyserial
```

_**Note:** Packaged releases already come with the prerequisites and thus do not need additional software setup other than fulfilling the minimum operating system requirements for the 3.10 version of Python._

The current implementation supports the commands used by the following list of devices, which receive the **XM service** by Sirius XM Radio LLC.

Further support for other devices may be implemented in the future.

| Device | Baud Rate |
| :- | -: |
| [PCR](https://en.wikipedia.org/wiki/XM_PCR) | 9600 |
| Direct | 9600 |
| Commander | 9600 |
| [WxWorx](https://www.wxworx.com/) (Portable) | 38400 |
| WxWorx (Certified) | 115200 |

## Setup
The program can be run standalone via the main script or by using [the latest packaged executable from the releases page](https://github.com/canisat/canipy/releases).

**Windows**

Simply download the EXE, or alternatively can run from source following the instructions.

You can identify which COM port corresponds to the radio's serial controller through Device Manager.

**Mac**

Download the source code package and run the script using Terminal following the steps.

Your serial port device path should be designated as `/dev/cu.usbserial*` or `/dev/tty.usbserial*`.

**Linux**

Download the source code package and run the script from your shell in a graphical environment following the steps.

Your serial port device path should be designated as `/dev/ttyUSB*` or `/dev/ttyS*`.

## Usage

1. Connect the tuner to the computer.
2. Start the GUI from the script (`python3 main.py`) or by running the packaged executable.
3. Verify the device's COM/TTY port path. If the device is using a different port, change it first in the top-left input box.
4. Select the corresponding device from the drop-down menu and power it on.
5. Change channels if needed by entering the channel number on the channel input field and clicking the button underneath.
6. Power off when done.

## Module
To use CaniPy as an extension for your own project, if using Git for version tracking, it is possible to add this as a submodule (`git submodule add //link/to/canisat.git`). Otherwise, simply download this repo and add the root contents to a `canipy` directory located in your code root.

Once CaniPy is added to a project, import it to the script using `from canipy import CaniPy` and start a `CaniPy()` instance.

## Why Python?
CaniPy takes advantage of Python's more legible syntax for others to better understand the control commands that the supported hardware can understand.

## Notice
This codebase is derived from [PyXM](https://github.com/timcanham/PyXM) by Timothy Canham, under the Apache 2.0 license.

Serial commands were documented from both current CaniSat research and prior work conducted by [Nick Sayer](https://sourceforge.net/u/nsayer/profile/), the linuXMPCR and Perl XM PCR projects, Hybrid Mobile Technologies, and the defunct XM Fan forums.

CaniSat, a non-profit initiative, and its incubator [NetOtt Solutions, LLC](https://netott.com/) are not affiliated with either Sirius XM Holdings Inc., Sirius XM Radio LLC, or any of its products, partners, or subsidiaries. Sirius, XM, SiriusXM and all related indicia are trademarks of Sirius XM Holdings Inc.

The data products distributed in the service(s) are intended to be supplemental and advisory per the provider. It is not recommended for use in circumstances that require immediate urgency to fulfill safety-critical work. Both CaniSat and the service provider are not responsible for errors and inaccuracies encountered when utilizing the service data products.

CaniSat does not condone or encourage the use of its affiliated projects for unauthorized copying, duplication, or distribution of copyrighted materials received through the supported services. The end user is solely responsible for ensuring their activities comply with applicable copyright laws and service terms. Don't steal music.
