# CaniPy
Serial SDARS receiver control in Python.

CaniPy provides a modern foundation for hobbyists to continue using supported SDARS hardware.

The project can either be used by itself, currently a prototype GUI for both regular use and as a code sample, or as a module that can be imported to support other scripts.

## Requirements
Python 3.10 or higher is required to run the code.

The current implementation supports the commands used by these devices, which receive the **XM service** by Sirius XM Radio LLC.

Further support for other devices may be implemented in the future.

| Device | Baud Rate |
| :- | -: |
| [PCR](https://en.wikipedia.org/wiki/XM_PCR) | 9600 |
| Direct | 9600 |
| Commander | 9600 |
| [WxWorx](https://www.wxworx.com/) (Portable) | 38400 |
| WxWorx (Certified) | 115200 |

## Why Python?
CaniPy takes advantage of Python's ease of code legibility for others to better understand the control commands of the supported hardware.

## External Libraries
* [pySerial](https://pypi.org/project/pyserial/)

## Notice
This codebase is derived from [PyXM](https://github.com/timcanham/PyXM) by Timothy Canham, under the Apache 2.0 license.

Serial commands were documented from both current CaniSat research and prior work conducted by [Nick Sayer](https://sourceforge.net/u/nsayer/profile/), the linuXMPCR and Perl XM PCR projects, Hybrid Mobile Technologies, and the defunct XM Fan forums.

CaniSat, a non-profit initiative, and its incubator [NetOtt Solutions, LLC](https://netott.com/) are not affiliated with either Sirius XM Holdings Inc., Sirius XM Radio LLC, or any of its products, partners, or subsidiaries. Sirius, XM, SiriusXM and all related indicia are trademarks of Sirius XM Holdings Inc.

The data products distributed in the service(s) are intended to be supplemental and advisory per the provider. It is not recommended for use in circumstances that require immediate urgency to fulfill safety-critical work. Both CaniSat and the service provider are not responsible for errors and inaccuracies encountered when utilizing the service data products.

CaniSat does not condone or encourage the use of its affiliated projects for unauthorized copying, duplication, or distribution of copyrighted materials received through the supported services. The end user is solely responsible for ensuring their activities comply with applicable copyright laws and service terms. Don't steal music.
