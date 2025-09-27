# CaniPy
Serial SDARS receiver control in Python.

CaniPy provides a modern foundation for allowing continued use of supported SDARS hardware by hobbyists.

The project can either be used by itself, currently a prototype GUI for both regular use and as a code sample, or as a module that can be imported to support other scripts.

## Requirements
Python 3.10 or higher is required to run the code.

The current version supports the commands used by these devices that receive the **XM service** by Sirius XM Radio LLC.

Further support for other devices may be implemented in the future.

| Device | Baud Rate |
| :- | -: |
| [PCR](https://en.wikipedia.org/wiki/XM_PCR) | 9600 |
| Direct | 9600 |
| Commander | 9600 |
| [WxWorx](https://www.wxworx.com/) (Portable) | 38400 |
| WxWorx (Certified) | 115200 |

## Why Python?
CaniPy is intended to use the better legibility of Python to simplify porting and understanding of the control commands for the supported hardware.

## Libraries
* [tkinter](https://docs.python.org/3/library/tkinter.html)
* [pySerial](https://pypi.org/project/pyserial/)

## Notice
This codebase is derived from [PyXM](https://github.com/timcanham/PyXM) by Timothy Canham, under the Apache 2.0 license.

Serial commands were documented from past research conducted by [Nick Sayer](https://sourceforge.net/u/nsayer/profile/), the linuXMPCR and Perl XM PCR projects, Hybrid Mobile Technologies, and the defunct XM Fan forums.

CaniSat, a non-profit initiative, and its incubator [NetOtt Solutions, LLC](https://netott.com/) are not affiliated with either Sirius XM Radio LLC or its products & partners. Sirius, XM, SiriusXM and all related indicia are trademarks of Sirius XM Radio LLC.

CaniSat does not condone or encourage the use of the software suite for unauthorized copying, duplication, or distribution of copyrighted materials received through the supported services. The end user is solely responsible for ensuring their activities comply with applicable copyright laws and service terms. Don't steal music.
