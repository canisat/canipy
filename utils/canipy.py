import serial

from collections.abc import Callable

from .comm.canirx import CaniRX
from .comm.canitx import CaniTX
from .comm.special.canidx import CaniDX
from .comm.special.caniwx import CaniWX

class CaniPy:
    """
    The main CaniPy support script, used to interface with supported SDARS hardware.

    Args:
        port (str, optional): The path of the serial to use (COM3, /dev/ttyUSB0, etc). Default to no path.
        baud (int, optional): The baud rate (bits/second) to use. Default to 9600 baud.

    Attributes:
        header (bytes): Request/response header constant indicating the start of a supported packet (5A A5, hex).
        tail (bytes): Request footer constant indicating the end of a supported packet (ED ED, hex).

        port_name (str): Indicates the assigned/active serial device path.
        baud_rate (int): Indicates the assigned/active serial baud rate.

        verbose (bool): Toggle for identifying whether to display additional information for debugging purposes.

        ch_num (int): Assigned/display number for the currently tuned channel.
        ch_sid (int): Raw ID for the currently tuned channel, relative to its place in the satellite feed.
        ch_name (str): Display name for the currently tuned channel.

        artist_name (str): Line 1 of the display information, usually the name of the artist/group/composer.
        title_name (str): Line 2 of the display information, usually the name of the song/program.

        cat_name (str): Display name for the current channel's assigned category (Rock, Pop, News, etc).
        cat_id (int): The ID number corresponding to the current channel's assigned category.

        sig_strength (int): Overall satellite signal strength (Exp: -1 inactive, 0 none, 1 low, 2 med, 3 hi).
        ant_strength (int): Indicates whether the antenna is connected or not (Exp: -1 inactive, 0 none, 3 connected).
        ter_strength (int): Overall terrestrial signal strength (Exp: -1 inactive, 0 none, 1 low, 2 med, 3 hi).

        self.radio_id (str): The ID of the tuner hardware assigned by the service provider.

        direct_idleframes (int): Counter for every time the Direct reports F2 hex.

        rx (CaniRX): Functions related to receipt of responses.
        tx (CaniTX): Functions related to transmission of commands.
        dx (CaniDX): Functions related to Direct receiver commands.
        wx (CaniWX): Functions related to data commands, notably to weather data receivers.

        serial_conn (serial.Serial): The active serial connection used for interfacing the radio.
    
    Lambda:
        set_port(): Set up a new connection, only changing the serial device path.
        set_baud(): Set up a new connection, only changing the baud rate.
    """

    def __init__(self, port:str="", baud:int=9600):
        self.header = bytes([0x5A, 0xA5])
        self.tail = bytes([0xED, 0xED])

        self.port_name = port
        self.baud_rate = baud

        # Verbose output toggle
        self.verbose = False

        # Audio and signal info
        # Assume radios start at 0
        self.ch_num = 0
        self.ch_sid = 0
        self.ch_name = ""

        self.artist_name = ""
        self.title_name = ""

        self.cat_name = ""
        self.cat_id = 0

        self.sig_strength = -1
        self.ant_strength = -1
        self.ter_strength = -1

        self.radio_id = ""

        self.direct_idleframes = 0

        self.serial_conn = None
        if port: self.set_serial_params(port, baud)

        self.set_port = lambda new_port: self.set_serial_params(new_port, self.baud_rate)
        self.set_baud:Callable[[int], None] = lambda new_baud: self.set_serial_params(self.port_name, new_baud)

        self.rx = CaniRX(self)
        self.tx = CaniTX(self)
        self.dx = CaniDX(self)
        self.wx = CaniWX(self)

        print("CaniPy started")

    def set_serial_params(self, port:str, baud:int):
        """
        Configure a new connection to the serial device.

        Args:
            port (str): The serial device's path or identifier.
            baud (int): The baud rate of the connection.
        """
        self.port_name = port
        self.baud_rate = baud
        try:
            self.serial_conn = serial.Serial(port=port, baudrate=baud, timeout=1)
        except serial.SerialException:
            print(f"Port is unavailable")
            self.serial_conn = None

    def close(self):
        """
        Close the connection to the serial device.
        """
        if self.serial_conn is None or not self.serial_conn.is_open:
            print("Port already closed")
            return
        self.serial_conn.close()
