# CaniPy
Serial SDARS receiver control in Python.

CaniPy provides a modern foundation for allowing continued use of supported SDARS hardware by hobbyists.

The project at this time is comprised of both a prototype GUI and auxiliary test-bed code to be implemented, upgrading from older Python 2 syntax over to Python 3.

## Devices
The current version contains implementations that support these devices using Sirius XM Radio LLC's **XM network**.

Further support for other devices may be implemented in the future.

| Device | Baud Rate |
| :- | -: |
| [PCR](https://en.wikipedia.org/wiki/XM_PCR) | 9600 |
| Direct | 9600 |
| Commander | 9600 |
| [WxWorx](https://www.wxworx.com/) (Portable) | 38400 |
| WxWorx (Certified) | 115200 |

## Why Python?
CaniPy is intended to provide a legible foundation for understanding the control commands and behavior applicable to the supported SDARS serial devices.

## Libraries
* [tkinter](https://docs.python.org/3/library/tkinter.html)
* [pySerial](https://pypi.org/project/pyserial/)

## Notice
This codebase is derived from [PyXM](https://github.com/timcanham/PyXM) by Timothy Canham, under the Apache 2.0 license.

Serial commands were documented from past research conducted by [Nick Sayer](https://sourceforge.net/u/nsayer/profile/), the linuXMPCR and Perl XM PCR projects, Hybrid Mobile Technologies, and the former XM Fan forums.

CaniSat is a non-profit initiative incubated by [NetOtt Solutions, LLC](https://netott.com/).

Sirius, XM, SiriusXM and all related indicia are trademarks of Sirius XM Radio LLC.

CaniSat and NetOtt are not affiliated with Sirius XM Radio LLC or its products & partners.
