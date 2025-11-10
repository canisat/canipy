import serial

from datetime import datetime, timezone

from collections.abc import Callable

from .comm import CaniRX, CaniTX, CaniConductor, CaniThread, CaniDX, CaniWX

class CaniPy:
    """
    The main CaniPy support script, used to interface with supported SDARS hardware.

    Args:
        port (str, optional): The path of the serial to use (COM3, /dev/ttyUSB0, etc). Default to no path.
        baud (int, optional): The baud rate (bits/second) to use. Default to 9600 baud.
        gui (optional): Reference an external subsystem for output if provided. Default to None.

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

        ticker (str): Text used for scrolling information.

        sig_strength (int): Overall satellite signal strength (Exp: -1 inactive, 0 none, 1 low, 2 med, 3 hi).
        ant_strength (int): Indicates whether the antenna is connected or not (Exp: -1 inactive, 0 none, 3 connected).
        ter_strength (int): Overall terrestrial signal strength (Exp: -1 inactive, 0 none, 1 low, 2 med, 3 hi).

        sat_datetime (datetime): Stores the date-time value from the service when reported by the radio.

        data_in_use (bool): Flag to identify if data mode is enabled or disabled.

        radio_id (str): The ID of the tuner hardware assigned by the service provider.

        direct_idleframes (int): Counter for every time the Direct reports F2 hex.

        rx (CaniRX): Functions related to receipt of responses.
        tx (CaniTX): Functions related to transmission of commands.
        dx (CaniDX): Functions related to Direct receiver commands.
        wx (CaniWX): Functions related to data commands, notably to weather data receivers.
        conductor (CaniConductor): Relays received responses to corresponding functions.

        thread (CaniThread): Threaded instance reading the port for responses from the radio.

        gui: A referenced subsystem class for directing output to it instead of a terminal.

        serial_conn (serial.Serial): The active serial connection used for interfacing the radio.
    
    Lambda:
        set_port(): Set up a new connection, only changing the serial device path.
        set_baud(): Set up a new connection, only changing the baud rate.
    """
    def __init__(self, port:str="", baud:int=9600, gui=None):
        self.header = bytes([0x5A, 0xA5])
        self.tail = bytes([0xED, 0xED])

        self.port_name = port
        self.baud_rate = baud

        # Verbose output toggles
        self.verbose = False
        self.clock_logging = False

        # Audio and signal info
        # Assume radios start at 0
        self.ch_num = 0
        self.ch_sid = 0
        self.ch_name = ""

        self.artist_name = ""
        self.title_name = ""

        self.cat_name = ""
        self.cat_id = 0

        self.ticker = ""

        self.sig_strength = -1
        self.ant_strength = -1
        self.ter_strength = -1

        # Assume minimum date value means not set
        self.sat_datetime = datetime(1900,1,1,tzinfo=timezone.utc)

        self.data_in_use = False

        self.radio_id = ""

        self.direct_idleframes = 0

        self.serial_conn = None

        self.set_port = lambda new_port: self.open(new_port, self.baud_rate)
        self.set_baud:Callable[[int], None] = lambda new_baud: self.open(self.port_name, new_baud)

        self.rx = CaniRX(self)
        self.tx = CaniTX(self)
        self.dx = CaniDX(self)
        self.wx = CaniWX(self)
        self.conductor = CaniConductor(self)

        self.thread = CaniThread(self)

        self.gui = gui

        if port: self.open(port, baud)

        self.logprint("CaniPy started")
    
    def __del__(self):
        """
        Halt thread and close connection when object is destroyed.
        """
        # Stop verbose output when destroyed
        self.verbose = False
        self.close()

    def reset_display(self):
        """
        Resets all display values stored by the instance.
        """
        self.ch_num = 0
        self.ch_sid = 0
        self.ch_name = ""
        self.artist_name = ""
        self.title_name = ""
        self.cat_name = ""
        self.cat_id = 0
        self.ticker = ""
        self.sig_strength = -1
        self.ant_strength = -1
        self.ter_strength = -1
        self.sat_datetime = datetime(1900,1,1,tzinfo=timezone.utc)
        self.data_in_use = False
        self.radio_id = ""

    def open(self, port:str, baud:int):
        """
        Configure a new connection to the serial device.

        Args:
            port (str): The serial device's path or identifier.
            baud (int): The baud rate of the connection.
        """
        # stop thread if one already exists
        self.thread.stop()
        self.port_name = port
        self.baud_rate = baud
        try:
            self.serial_conn = serial.Serial(port=port, baudrate=baud, timeout=1)
        except serial.SerialException:
            self.errorprint("Device port is unavailable")
            self.serial_conn = None
            return
        # start com port read thread
        self.thread.start()
        
    def close(self):
        """
        Close the connection to the serial device.
        """
        # clear display vars
        self.reset_display()
        # stop thread
        self.thread.stop()
        if self.serial_conn is None or not getattr(self.serial_conn,"is_open",False):
            if self.verbose: self.logprint("Port already closed")
            return
        self.serial_conn.close()

    def infoprint(self, msg:str):
        """
        Send information to a subsystem if any, otherwise print to shell.

        Args:
            msg (str): The message to output
        """
        self.gui.infobox(msg) if self.gui else print(msg)

    def warnprint(self, msg:str):
        """
        Send warning to a subsystem if any, otherwise print to shell.

        Args:
            msg (str): The message to output
        """
        self.gui.warnbox(msg) if self.gui else print(msg)

    def errorprint(self, msg:str):
        """
        Send error to a subsystem if any, otherwise print to shell.

        Args:
            msg (str): The message to output
        """
        self.gui.errorbox(msg) if self.gui else print(msg)
    
    def logprint(self, msg:str):
        """
        Send log message to a subsystem if any, otherwise print to shell.

        Args:
            msg (str): The message to output
        """
        self.gui.logbox(msg) if self.gui else print(msg)
