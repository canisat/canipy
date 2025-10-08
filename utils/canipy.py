import serial

from collections.abc import Callable

from .canirx import CaniRX
from .canitx import CaniTX
from .special.canidx import CaniDX
from .special.caniwx import CaniWX

class CaniPy:
    """
    The main CaniPy support script, used to interface with supported SDARS hardware.

    Args:
        port (str, optional): The path of the serial to use (COM3, /dev/ttyUSB0, etc). Default to no path.
        baud (int, optional): The baud rate (bits/second) to use. Default to 9600 baud.

    Attributes:
        header (bytes): Request/response header indicating the start of a supported packet (5A A5, hex).
        tail (bytes): Request footer indicating the end of a supported packet (ED ED, hex).

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
        mute(): Mutes audio.
        unmute(): Unmutes audio.

        sigmon_enable(): Enable signal monitoring.
        sigmon_disable(): Disable signal monitoring.

        chanmon_disable(): Disable channel monitoring.

        diagmon_enable(): Enable diagnostics info monitoring.
        diagmon_disable(): Disable diagnostics info monitoring.

        wx_datastop(): Instructs the radio to halt data RX.

        curr_channel_info(): Prompts radio to report info for current channel.
        next_channel_info(): Prompts radio to report info for the channel ahead of the current one.
        prev_channel_info(): Prompts radio to report info for the channel behind the current one.

        curr_ext_info(): Prompts radio to report extended program info for current channel.

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

        self.rx = CaniRX(self)
        self.tx = CaniTX(self)
        self.dx = CaniDX(self)
        self.wx = CaniWX(self)

        self.serial_conn = None
        if port: self.set_serial_params(port, baud)

        self.mute = lambda: self.tx.set_mute(True)
        self.unmute = lambda: self.tx.set_mute(False)

        self.sigmon_enable = lambda: self.tx.signal_mon(True)
        self.sigmon_disable = lambda: self.tx.signal_mon(False)

        self.chanmon_disable = lambda: self.tx.chan_mon(0)

        self.diagmon_enable = lambda: self.tx.diag_mon(True)
        self.diagmon_disable = lambda: self.tx.diag_mon(False)

        self.wx_datastop = lambda: self.wx.change_datachan(0xFF, True, True)

        self.curr_channel_info = lambda: self.tx.channel_info(self.ch_num)
        self.next_channel_info = lambda: self.pcr_tx(bytes([0x25, 0x09, self.ch_num, 0x00]))
        self.prev_channel_info = lambda: self.pcr_tx(bytes([0x25, 0x0A, self.ch_num, 0x00]))

        self.curr_ext_info = lambda: self.tx.ext_info(self.ch_num)

        self.set_port = lambda new_port: self.set_serial_params(new_port, self.baud_rate)
        self.set_baud:Callable[[int], None] = lambda new_baud: self.set_serial_params(self.port_name, new_baud)

        print("CaniPy started")

    def pcr_tx(self, payload:bytes) -> bytes:
        """
        Prepares and transmits a packet to be sent to the radio.
        Takes a bare payload and encloses it with the necessary header, length, and footer.

        Example:
            A payload of "31" is provided to fetch the radio ID.
            5A A5 & two-byte length of the payload (1 byte) are added as the prefix, then ED ED as the suffix.
            The resulting transmission is "5A A5 00 01 31 ED ED".

        Args:
            payload (bytes): A command, comprised as a set of bytes, to be encased and sent to the radio.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.serial_conn is None or not self.serial_conn.is_open:
            print("No serial port in use")
            return b""
        length = len(payload).to_bytes(2, byteorder='big')
        command = self.header + length + payload + self.tail
        self.serial_conn.write(command)
        if self.verbose:
            print(f"Sent: {' '.join(f'{b:02X}' for b in payload)}")
        return payload

    def rx_response(self, payload:bytes):
        """
        Takes in a response payload to then determine and display the information stored within it.
        The message type is checked to select how to handle it.

        Args:
            payload (bytes): A response, comprised as a set of bytes, to parse the information from.
        """
        # payload[1] and payload[2] appear to
        # always be status code and detail respectively,
        # except if it's an event driven response.
        match payload[0]:
            case 0x80:
                self.rx.parse_startup(payload)
            case 0x81:
                print("Goodnight")
            case 0x8b:
                # TODO: Printout to scale of -96dB to 24dB
                print(f"Line level set to -{payload[3]}dB")
            case 0x90:
                if payload[1] == 0x03:
                    print("Not subscribed")
                    if payload[2] == 0x09:
                        print("Contact service provider to subscribe")
                    elif payload[2] == 0x0a:
                        print("Not available for current subscription")
                    return
                if payload[1] == 0x04:
                    print("No signal")
                    if payload[2] == 0x10:
                        print("Check if antenna is connected")
                        print("and has a clear view of the sky")
                    return
                self.ch_sid = payload[3]
                self.ch_num = payload[4]
                if self.verbose: print(f"SID {payload[3]}, Ch. {payload[4]}")
                if payload[5]:
                    # When first tuning to a data channel, like
                    # main WX SID 240, this will still be 0. But tune
                    # normally to another channel after, this becomes 1.
                    # Might be to indicate auxiliary tuning is enabled
                    # to allow simultaneous audio and data tuning.
                    print(f"Data aux is on")
                    # 02 03 indicates entitled data product
                    if payload[1] == 0x02 and payload[2] == 0x03:
                        print("Product is available with current subscription")
                self.tx.channel_info(payload[4])
            case 0x91:
                # Hacky way to distinguish, but if it's data, it's usually SID
                # Or maybe 11/91 is exclusively sid, im not sure...
                # TODO: Check this is working right in normal operation!
                if payload[4]:
                    self.ch_sid = payload[3]
                else:
                    self.ch_num = payload[3]
                print("Current channel tune cancelled! You will be tuned out!")
                if payload[3]:
                    print(f"Ready for channel {payload[3]}{' (Data)' if payload[4] else ''}")
                print("Change channel to resume content")
            case 0x93:
                print(f"Mute: { {0x00:'Off',0x01:'On'}.get(payload[3],f'?({payload[3]})') }")
            case 0xA2:
                self.rx.parse_extinfo(payload)
            case 0xA5:
                self.rx.parse_chan(payload)
            case 0xB1:
                if len(payload) != 12:
                    print("Invalid Radio ID length")
                    if self.verbose: print(f"Exp 12, got {len(payload)}")
                    return
                # if good, print characters
                self.radio_id = payload[4:12].decode('utf-8')
                print(f"Radio ID: {payload[4:12].decode('utf-8')}")
            case 0xC1 | 0xC3:
                self.rx.parse_sig(payload)
            case 0xC2:
                print("Signal strength monitoring status updated")
            case 0xCA:
                # 'A' cmds are WX specific!
                if payload[1] == 0x40:
                    if payload[2] == 0xff:
                        print(f"WX - Error setting up data RX on {payload[4]}")
                        if payload[3] == 0x0a:
                            print("Data track not available for current subscription")
                        return
                    if payload[4] != 0xff:
                        print(f"WX - Ready for data from {payload[4]}")
                    else:
                        print("WX - Data stopped")
                    return
                if payload[1] == 0x43:
                    print("WX - Pong")
                    return
                if payload[1] == 0x64:
                    print(f"WX - Version: {payload[2:].decode('utf-8').rstrip(chr(0))}")
            case 0xD0:
                if payload[3]:
                    print(f"Monitoring channel {payload[3]}")
                    return
                print("Channel monitoring stopped")
            case 0xD1:
                if payload[2] == 0x01:
                    # Store only if channel numbers match!
                    if payload[1] == self.ch_num:
                        self.ch_name = payload[3:19].decode('utf-8')
                    print("===Channel Name===")
                    print(f"Channel {payload[1]}")
                    print(payload[3:19].decode('utf-8'))
                    # Trailing bytes, this could be length side effect?
                    # Like with whats happening with extended info?
                    # Treat as debug info for now.
                    if self.verbose:
                        print(' '.join(f'{b:02X}' for b in payload[19:]))
                    print("==================")
            case 0xD2:
                if payload[3] == 0x01:
                    if payload[1] == self.ch_num:
                        self.cat_id = payload[2]
                        self.cat_name = payload[4:].decode('utf-8')
                    print("===Ch. Category===")
                    print(f"Channel {payload[1]}")
                    print(payload[4:].decode('utf-8'))
                    if self.verbose:
                        print(f"Cat ID: {payload[2]:02X}")
                    print("==================")
            case 0xD3:
                if payload[2] == 0x01:
                    if payload[1] == self.ch_num:
                        self.artist_name = payload[3:19].decode('utf-8')
                        self.title_name = payload[19:].decode('utf-8')
                    print("===Program Info===")
                    print(f"Channel {payload[1]}")
                    print(payload[3:19].decode('utf-8'))
                    print(payload[19:].decode('utf-8'))
                    print("==================")
            case 0xD4:
                if payload[2] == 0x01:
                    if payload[1] == self.ch_num:
                        self.artist_name = payload[3:].decode('utf-8').rstrip(chr(0))
                    print("===Artist Info.===")
                    print(f"Channel {payload[1]}")
                    print(payload[3:].decode('utf-8').rstrip(chr(0)))
                    print("==================")
            case 0xD5:
                if payload[2] == 0x01:
                    if payload[1] == self.ch_num:
                        self.title_name = payload[3:].decode('utf-8').rstrip(chr(0))
                    print("===Title  Info.===")
                    print(f"Channel {payload[1]}")
                    print(payload[3:].decode('utf-8').rstrip(chr(0)))
                    print("==================")
            case 0xD6:
                if payload[3] == 0x01 or payload[4] == 0x01:
                    print("===Program Len.===")
                    print(f"Channel {payload[1]}")
                    if self.verbose:
                        print(f"Time Format: {payload[2]:02X}")
                    if payload[3] == 0x01:
                        print(f"Started {round(((payload[5] << 8) | payload[6])/60)}m ago")
                    if payload[4] == 0x01:
                        print(f"Ends in {round(((payload[7] << 8) | payload[8])/60)}m")
                    print("==================")
            case 0xDE:
                print("Clock monitoring status updated")
            case 0xDF:
                self.rx.parse_clock(payload)
            case 0xE0:
                print("Fetched activation info")
            case 0xE1:
                print("Fetched deactivation info")
            case 0xE3:
                self.rx.parse_firminf(payload)
            case 0xE4 | 0xF4:
                # Acknowledgement of Direct responses.
                # nsayer ref listens to E4 though?? differs by 4th opcode
                # TODO: cover both until better understood
                print("Direct command Acknowledged")
            case 0xEA:
                # Rudimentary data implementation.
                # Will only report if verbose logging.
                # TODO: Figure out how the data is to be written.
                if self.verbose:
                    if payload[1] == 0xD0:
                        print("=== DATA  INFO ===")
                        print(f"SID: {payload[2]}")
                        print(f"Frame: {payload[3]}")
                        # The radio packets in general can theoretically
                        # report up to 64k. Studied pcaps only go up to 220
                        # however, and a data frame that was inspected only
                        # went up to D0 (208 bytes), but data frames could
                        # be larger in theory?
                        print(f"Length: {payload[7]} bytes")
                        print("===    DATA    ===")
                        # Safely print out bare data
                        print(payload[10:].decode('utf-8', errors='replace'))
                        print("==================")
                        print("===    HEX!    ===")
                        # Print out hex dump
                        print(' '.join(f'{b:02X}' for b in payload[10:]))
                        print("==================")
                        return
                print("Data packet received")
            case 0xF0:
                print("Diagnostic info monitoring status updated")
            case 0xF1:
                if self.verbose:
                    # TODO: examine how diag is laid out, appears to be 8 or 9 fields
                    print("=== DIAGNOSTIC ===")
                    print(payload[2:].decode('utf-8'))
                    print("==================")
            case 0xF2:
                # Direct idle frames.
                # Counted, but generally just ignored.
                self.direct_idleframes += 1
            case 0xFF:
                print("Warning! Radio reported an error")
                if payload[1] == 0x01 and payload[2] == 0x00:
                    # 01 00 (aka OK) on error, typically corresponds to antenna
                    print("Antenna not detected, check antenna")
                if payload[1] == 0x02:
                    # 02 means radio is not repsonding
                    print("Radio unresponsive!")
                    if payload[2] == 0x04:
                        print("Unable to change channels")
                    elif payload[2] == 0x06:
                        print("Unable to change radio's power state")
                if payload[1] == 0x07 and payload[2] == 0x10:
                    # 07 10, sending commands to a radio tuner that is not on yet
                    print("Please power up the tuner before sending commands")
                if self.verbose:
                    print(f"{payload[1]:02X} {payload[2]:02X} {payload[3:].decode('utf-8')}")
                print("Radio may still be operated")
                print("If errors persist, check or power-cycle the radio")
            case _:
                print(f"Unknown return code {hex(payload[0])}")

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
