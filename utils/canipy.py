try:
    import serial
except:
    print("Serial Library not available")

import time
from collections.abc import Callable

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

        serial_conn (serial.Serial): The active serial connection used for interfacing the radio.
    
    Lambda:
        mute(): Mutes audio.
        unmute(): Unmutes audio.

        sigmon_enable(): Enable signal monitoring.
        sigmon_disable(): Disable signal monitoring.

        chanmon_disable(): Disable channel monitoring.

        diagmon_enable(): Enable diagnostics info monitoring.
        diagmon_disable(): Disable diagnostics info monitoring.

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

        self.mute = lambda: self.set_mute(True)
        self.unmute = lambda: self.set_mute(False)

        self.sigmon_enable = lambda: self.signal_mon(True)
        self.sigmon_disable = lambda: self.signal_mon(False)

        self.chanmon_disable = lambda: self.chan_mon(0, False, False, False, False)

        self.diagmon_enable = lambda: self.diag_mon(True)
        self.diagmon_disable = lambda: self.diag_mon(False)

        # TODO: These may be valid? if not, have 9 and 10
        # just increment in func & figure out what
        # to do with these here lambdas
        self.curr_channel_info = lambda: self.pcr_tx(bytes([0x25, 0x08]))
        self.next_channel_info = lambda: self.pcr_tx(bytes([0x25, 0x09]))
        self.prev_channel_info = lambda: self.pcr_tx(bytes([0x25, 0x10]))

        # TODO: I think just sending 22 would imply current channel?
        self.curr_ext_info = lambda: self.pcr_tx(bytes([0x22]))

        self.set_port = lambda new_port: self.set_serial_params(new_port, self.baud_rate)
        self.set_baud:Callable[[int], None] = lambda new_baud: self.set_serial_params(self.port_name, new_baud)

        self.serial_conn = None
        if port: self.set_serial_params(port, baud)

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
        if self.serial_conn is None:
            print("No serial port in use")
            return b""
        length = len(payload).to_bytes(2, byteorder='big')
        command = self.header + length + payload + self.tail
        self.serial_conn.write(command)
        if self.verbose:
            print(f"Sent: {' '.join(f'{b:02X}' for b in payload)}")
        return payload

    def rx_startup(self, payload:bytes):
        """
        Takes in a power-on event response (80 hex) to print out relevant information.
        At this time, verification of the command is by checking if it contains 27 bytes.

        Args:
            payload (bytes): A response, comprised as a set of bytes, to parse the information from.
        """
        if len(payload) == 27:
            self.radio_id = payload[19:27].decode('utf-8')
            print("===Radio Info===")
            print(f"Activated: {'No' if payload[1] == 0x3 else 'Yes'}")
            # No idea what payload[3] might be yet, always 0 in pcaps.
            # Ignoring it for now.
            if self.verbose:
                print(f"RX Version: {'.'.join(list(str(payload[4])))}")
                print(f"RX Date: {payload[5]:02X}/{payload[6]:02X}/{payload[7]:02X}{payload[8]:02X}")
                print(f"Last SID 1: {payload[9]:02X}{' (Data)' if payload[10] else ''}")
                print(f"Last SID 2: {payload[11]:02X}{' (Data)' if payload[12] else ''}")
                print(f"CMB Version: {'.'.join(list(str(payload[13])))}")
                print(f"CMB Date: {payload[14]:02X}/{payload[15]:02X}/{payload[16]:02X}{payload[17]:02X}")
            print(f"Radio ID: {payload[19:27].decode('utf-8')}")
            print("================")
            return
        print("Payload not of correct length")
        if self.verbose: print(f"Exp 27, got {len(payload)}")

    def rx_chan(self, payload:bytes):
        """
        Takes in a channel info response (A5 hex) to print out relevant information.
        Relevant channel information is stored in respective attributes before printout.
        At this time, verification of the command is by checking if it contains 77 bytes.

        Args:
            payload (bytes): A response, comprised as a set of bytes, to parse the information from.
        """
        if len(payload) == 77:
            # Assign values if it's the current channel
            is_currchan = False
            if payload[3] == self.ch_num or payload[4] == self.ch_sid:
                # If number or SID match, we're in this channel.
                # Store values again to ensure they're up to speed.
                is_currchan = True
                self.ch_num = payload[3]
                self.ch_sid = payload[4]
            print("===Channel Info===")
            print(f"Channel {payload[3]}")
            if payload[1] == 0x03:
                print("Not subscribed")
                if payload[2] == 0x09:
                    print("Contact service provider to subscribe")
                print("==================")
                return
            if payload[5]:
                if is_currchan:
                    self.ch_name = payload[6:22].decode('utf-8')
                print(payload[6:22].decode('utf-8'))
            if payload[40]:
                if is_currchan:
                    self.artist_name = payload[41:57].decode('utf-8')
                    self.title_name = payload[57:73].decode('utf-8')
                print(payload[41:57].decode('utf-8'))
                print(payload[57:73].decode('utf-8'))
            if payload[22]:
                if is_currchan:
                    self.cat_name = payload[24:40].decode('utf-8')
                    self.cat_id = payload[23]
                print(payload[24:40].decode('utf-8'))
                if self.verbose: print(f"Cat ID: {payload[23]:02X}")
            if self.verbose: print(f"Service ID: {payload[4]:02X}")
            print("==================")
            return
        print("Payload not of correct length")
        if self.verbose: print(f"Exp 77, got {len(payload)}")

    def rx_extinfo(self, payload:bytes):
        """
        Takes in a extended label response (A2 hex) to print out relevant information.
        Relevant program information is stored in respective attributes before printout.
        At this time, verification of the command is by checking if it contains 78 bytes
        as community implementations read extended length assuming 0x24 label size was
        passed during power-on. Given how setting it to another length before caused
        strange results, I think it was deliberately set to 0x24 to work around a glitch
        with the tuner firmware. Function will only report 32 of the 36 bytes per line,
        following what other community projects have done.

        Args:
            payload (bytes): A response, comprised as a set of bytes, to parse the information from.
        """
        if len(payload) == 78:
            print("===Title  Info.===")
            print(f"Channel {payload[3]}")
            if payload[1] == 0x03:
                print("Not subscribed")
                if payload[2] == 0x09:
                    print("Contact service provider to subscribe")
                print("==================")
                return
            if payload[4]:
                if payload[3] == self.ch_num:
                    self.artist_name = payload[5:37].decode('utf-8').rstrip(chr(0))
                print(payload[5:37].decode('utf-8').rstrip(chr(0)))
                if self.verbose: print(' '.join(f'{b:02X}' for b in payload[37:41]))
            if payload[41]:
                if payload[3] == self.ch_num:
                    self.title_name = payload[57:73].decode('utf-8').rstrip(chr(0))
                print(payload[42:74].decode('utf-8').rstrip(chr(0)))
                if self.verbose: print(' '.join(f'{b:02X}' for b in payload[74:]))
            print("==================")
            return
        print("Payload not of correct length")
        if self.verbose: print(f"Exp 78, got {len(payload)}")

    def rx_sig(self, payload:bytes):
        """
        Takes in a signal info response (C1 or C3 hex) to print out relevant information.
        Relevant signal strength information is stored in respective attributes before printout.
        At this time, verification of the command is by checking if it contains 22 or 26 bytes.

        Args:
            payload (bytes): A response, comprised as a set of bytes, to parse the information from.
        """
        if len(payload) in (22, 26):
            if payload[0] == 0xC1:
                # If C1 event-driven poll, pad it to conform
                payload = payload[:1] + bytes([1,0]) + payload[1:] + bytes(2)
            # Store signal info
            self.sig_strength = payload[3]
            self.ant_strength = payload[4]
            self.ter_strength = payload[5]
            siglabel = {0x00:"None",0x01:"Fair",0x02:"Good",0x03:"Excellent"}
            antlabel = {0x00:"Disconnected",0x03:"Connected"}
            print("===Receiver===")
            print(f"Sat: {siglabel.get(payload[3],f'?({payload[3]})')}")
            print(f"Ant: {antlabel.get(payload[4],f'?({payload[4]})')}")
            print(f"Ter: {siglabel.get(payload[5],f'?({payload[5]})')}")
            if self.verbose:
                # Additional info for rock & roll signal, plus terrestrial
                print("===QPSK/MCM===")
                # Demod lock
                print(f"Sat1: {'Locked' if payload[6] else 'Lost'}")
                print(f"Sat2: {'Locked' if payload[7] else 'Lost'}")
                print(f"Terr: {'Locked' if payload[8] else 'Lost'}")
                print("=====TDM!=====")
                # TDM lock
                print(f"Sat1: {'Locked' if payload[9] else 'Lost'}")
                print(f"Sat2: {'Locked' if payload[10] else 'Lost'}")
                print(f"Terr: {'Locked' if payload[11] else 'Lost'}")
                print("=====BER!=====")
                # Bit error rate is two bytes big,
                # 68ths, not exceeding 100%
                print(f"Sat1: {min(((payload[12] << 8) | payload[13]) / 68, 100):.2f}%")
                print(f"Sat2: {min(((payload[14] << 8) | payload[15]) / 68, 100):.2f}%")
                print(f"Terr: {min(((payload[16] << 8) | payload[17]) / 68, 100):.2f}%")
                print("=====AGC!=====")
                print(f"Sat: {payload[22]}")
                print(f"Ter: {payload[23]}")
                if payload[0] == 0xC3:
                    print("======CN======")
                    # C:N's are stored in 1/4 dB
                    print(f"Sat1: {payload[24]/4}")
                    print(f"Sat2: {payload[25]/4}")
            print("==============")
            return
        print("Payload not of correct length")
        if self.verbose: print(f"Exp 22 or 26, got {len(payload)}")

    def rx_firminf(self, payload:bytes):
        """
        Takes in a firmware info response (E3 hex) to print out relevant information.
        At this time, verification of the command is by checking if it contains 19 bytes.

        Args:
            payload (bytes): A response, comprised as a set of bytes, to parse the information from.
        """
        if len(payload) == 19:
            print("===FirmwareInfo===")
            # TODO: Versioning will need to be examined again.
            # I don't have the PCR with me at the moment...
            # For now, just print whatever
            print(f"SDEC Version: {'.'.join(list(str(payload[3])))}, {'.'.join(list(str(payload[4])))}")
            print(f"SDEC Date: {payload[5]:02X}/{payload[6]:02X}/{payload[7]:02X}{payload[8]:02X}")
            print(f"CMB Version: {'.'.join(list(str(payload[9])))}")
            print(f"CMB Date: {payload[10]:02X}/{payload[11]:02X}/{payload[12]:02X}{payload[13]:02X}")
            print(f"RX Version: {'.'.join(list(str(payload[14])))}")
            print(f"RX Date: {payload[15]:02X}/{payload[16]:02X}/{payload[17]:02X}{payload[18]:02X}")
            return
        print("Payload not of correct length")
        if self.verbose: print(f"Exp 19, got {len(payload)}")
    
    def rx_clock(self, payload:bytes, miltime:bool=False):
        """
        Takes in a time info response (DF hex) to print out relevant information.
        At this time, verification of the command is by checking if it contains 19 bytes.

        Args:
            payload (bytes): A response, comprised as a set of bytes, to parse the information from.
            miltime (bool, optional): Report the time in 24-hour format. Default to false.
        """
        # TODO: Ensure data is consistent!
        # Day will not be correct after around the 15th-16th!!!
        # This is a semi-long-term analysis!
        # Issues are expected!
        weekdaylabel = {
            0x02:"Monday",
            0x04:"Tuesday",
            0x06:"Wednesday",
            0x08:"Thursday",
            0x0A:"Friday",
            0x0C:"Saturday",
            0x0E:"Sunday"
        }
        if len(payload) == 11:
            print("===  DateTime  ===")
            weekdaycalc = (payload[4]>>4) - ((payload[4]>>4) % 2)
            # Day of the week
            print(f"{weekdaylabel.get(weekdaycalc,f'?({payload[4]})')}")
            # Funny layout to compensate the need to decode
            # Date
            print(f"{payload[1]:02d}{payload[2]:02d}-{payload[3]:02d}-{(
                payload[4]&0x0F
            ):02d}")
            # Time
            print(f"{(
                ((payload[5] % 12) or 12) if not miltime else payload[5]
            ):02d}:{payload[6]:02d}:{(
                payload[7] - 0x80 if payload[7] & 0x80 else payload[7]
            ):02d}{(
                ' PM' if payload[5] >= 12 else ' AM'
            ) if not miltime else ''} UTC")
            if self.verbose:
                # Seconds have high bit on for some reason...
                # TODO: Figure out why this is.
                # For now, AM and PM are determined by 24h time.
                # I thought this was an AM PM indicator at first.
                print(f"Raw seconds due to high bit: {payload[7]:02X}")
                print(f"Tick is at {payload[10]:02X}, rolled over {payload[9]} times.")
                print(f"Roll-over cleared {payload[8]} times since epoch.")
            print("==================")
            return
        print("Payload not of correct length")
        if self.verbose: print(f"Exp 11, got {len(payload)}")

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
                self.rx_startup(payload)
            case 0x81:
                print("Goodnight")
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
                # Kind of an oddball hack to identify if tuning to data.
                # This byte is true if tuning by SID (10 01) regardless.
                # Assume SID tune corresponds to data anyway as it's
                # VERY rare having to change channel based on SID.
                if payload[5]:
                    # OK (01 00) used in Main WX SID 240
                    print(f"Data mode set on app {payload[3]} (Ch. {payload[4]})")
                    # 02 03 indicates entitled product
                    if payload[1] == 0x02 and payload[2] == 0x03:
                        print("Product is available with current subscription")
                else:
                    self.channel_info(payload[4])
            case 0x91:
                # Hacky way to distinguish, but if it's data, it's usually SID
                # Or maybe 11/91 is exclusively sid, im not sure...
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
                self.rx_extinfo(payload)
            case 0xA5:
                self.rx_chan(payload)
            case 0xB1:
                if len(payload) != 12:
                    print("Invalid Radio ID length")
                    if self.verbose: print(f"Exp 12, got {len(payload)}")
                    return
                # if good, print characters
                self.radio_id = payload[4:12].decode('utf-8')
                print(f"Radio ID: {payload[4:12].decode('utf-8')}")
            case 0xC1 | 0xC3:
                self.rx_sig(payload)
            case 0xC2:
                print("Signal strength monitoring status updated")
            case 0xCA:
                # 'A' cmds are WX specific!
                if payload[1] == 0x40:
                    if payload[2] == 0xff:
                        print("WX - Error when setting up data")
                        if payload[3] == 0x0a:
                            print("Data track not available for current subscription")
                    print(f"WX - Ready for data on {payload[4]}")
                elif payload[1] == 0x43:
                    print("WX - Pong")
                elif payload[1] == 0x64:
                    print(f"WX - Version: {payload[2:].decode('utf-8').rstrip(chr(0))}")
            case 0xD0:
                if payload[3]:
                    print(f"Monitoring channel {payload[3]}")
                else:
                    print("Channel monitoring stopped")
            case 0xD1:
                if payload[2]:
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
                if payload[3]:
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
                if payload[2]:
                    if payload[1] == self.ch_num:
                        self.artist_name = payload[3:19].decode('utf-8')
                        self.title_name = payload[19:].decode('utf-8')
                    print("===Program Info===")
                    print(f"Channel {payload[1]}")
                    print(payload[3:19].decode('utf-8'))
                    print(payload[19:].decode('utf-8'))
                    print("==================")
            case 0xD4:
                if payload[2]:
                    if payload[1] == self.ch_num:
                        self.artist_name = payload[3:].decode('utf-8').rstrip(chr(0))
                    print("===Artist Info.===")
                    print(f"Channel {payload[1]}")
                    print(payload[3:].decode('utf-8').rstrip(chr(0)))
                    print("==================")
            case 0xD5:
                if payload[2]:
                    if payload[1] == self.ch_num:
                        self.title_name = payload[3:].decode('utf-8').rstrip(chr(0))
                    print("===Title  Info.===")
                    print(f"Channel {payload[1]}")
                    print(payload[3:].decode('utf-8').rstrip(chr(0)))
                    print("==================")
            case 0xD6:
                if payload[3] or payload[4]:
                    print("===Program Len.===")
                    print(f"Channel {payload[1]}")
                    if self.verbose:
                        print(f"Time Format: {payload[2]:02X}")
                    if payload[3]:
                        print(f"Started {round(((payload[5] << 8) | payload[6])/60)}m ago")
                    if payload[4]:
                        print(f"Ends in {round(((payload[7] << 8) | payload[8])/60)}m")
                    print("==================")
            case 0xDE:
                print("Clock monitoring status updated")
            case 0xDF:
                self.rx_clock(payload)
            case 0xE0:
                print("Fetched activation info")
            case 0xE1:
                print("Fetched deactivation info")
            case 0xE3:
                self.rx_firminf(payload)
            case 0xE4 | 0xF4:
                # Acknowledgement of Direct responses.
                # nsayer ref listens to E4 though?? differs by 4th opcode
                # TODO: cover both until better understood
                print("Direct command Acknowledged")
            case 0xEA:
                print("Data packet received")  # TODO: In the future, dump data to a file
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

    def power_up(self, ch_lbl:int=16, cat_lbl:int=16, title_lbl:int=36, loss_exp:bool=True) -> bytes:
        """
        Sends in a command to power on the radio tuner.
        Defaults are 16 characters long for channel and category labels, and 36 for title label
        mainly due to a possible oversight with the radio firmware when fetching extended labels.

        Example:
            The radio will be provided with "00 10 10 24 01".
            Power up with 16 char channel and category label size, 36 char title size, expect loss of power.

        Args:
            ch_lbl (int, optional): Maximum channel label character length. Default to 16 (10 hex).
            cat_lbl (int, optional): Maximum category label character length. Default to 16 (10 hex).
            title_lbl (int, optional): Maximum program title label character length. Default to 36 (24 hex).
            loss_exp (bool, optional): Indicate if the tuner is in a board that may shut off without notice. Default to True.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        print("Powering up")
        return self.pcr_tx(bytes([0x00, ch_lbl, cat_lbl, title_lbl, loss_exp]))

    def power_down(self, pwr_sav:bool=False) -> bytes:
        """
        Sends in a command to power down the radio tuner.

        Example:
            The radio will be provided with "01 00".
            Power off, no power save.

        Args:
            pwr_sav (bool, optional): Set radio to a power saving state instead. Default to False.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        print("Powering down")
        return self.pcr_tx(bytes([0x01, pwr_sav]))

    def change_channel(self, channel:int, is_sid:bool=False, data:bool=False, prg_type:int=0) -> bytes:
        """
        Sends in a command to the tuner to switch to another channel based on assigned number or ID.
        Some channels (i.e. SID 240/F0) can even be tuned as data.

        Example:
            To tune to audio channel number 1, the radio will be provided with "10 02 01 00 00 01".
            Tunes to channel 1, no data, program type 0, route to audio port (1).

        Args:
            channel (int): The channel value.
            is_sid (bool, optional): Indicate if provided number is a service ID. Default to False.
            data (bool, optional): Indicate to tune channel as a data feed and route data to download terminal. Default to False.
            prg_type (int, optional): Program type. Magic value; all known instances just leave it at 0 so it's defaulted to 0.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if channel not in range(256):
            print("Invalid channel value")
            return b""
        print(f"Changing to {'channel' if not is_sid else 'ID'} {channel}{' (Data)' if data else ''}")
        if not is_sid:
            self.ch_num = channel
        else:
            self.ch_sid = channel
        return self.pcr_tx(bytes([0x10, 0x02 - is_sid, channel, data, prg_type, 0x01 + data]))

    def channel_info(self, channel:int, is_sid:bool=False, prg_type:int=0) -> bytes:
        """
        Sends in a command to the tuner to report the channel's program information provided an assigned number or ID.

        Example:
            To check the info of channel number 1, the radio will be provided with "25 08 01 00".
            Report info for channel 1, program type 0.

        Args:
            channel (int): The channel value.
            is_sid (bool, optional): Indicate if provided number is a service ID. Default to False.
            prg_type (int, optional): Program type. Magic value; all known instances just leave it at 0 so it's defaulted to 0.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if channel not in range(256):
            print("Invalid channel value")
            return b""
        if self.verbose: print(f"Check RX for info on {channel}")
        # 07 allows for checking by SID
        return self.pcr_tx(bytes([0x25, 0x08 - is_sid, channel, prg_type]))

    def channel_cancel(self, channel:int=0, data:bool=False) -> bytes:
        """
        Sends in a command to the tuner to stop listening to the current channel, like picking up the needle off a record.
        The command then supplies a channel for the radio to "pre-load" and quickly tune after client processing.
        Additional byte is to indicate if the channel is for "pre-loading" in data mode.
        Running this will tune out of the current channel. User must tune once again to resume content.
        Channel number could just be the assigned number or service ID? No idea...
        This is mainly used for data channels to stop/finish data download before the channel loops the data.
        This command was not community documented, but is utilized by official implementations.

        Example:
            To stop listening and prepare the radio for channel 1, the radio will be provided with "11 01 00".
            Stop and prepare for channel 1, no data.

        Args:
            channel (int, optional): The channel value to preload. Default to 0 as in don't preload. Hopefully that'll work fine...
            data (bool, optional): Indicate to treat the preloaded channel as a data feed. Default to False.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if channel not in range(256):
            print("Invalid channel value")
            return b""
        if self.verbose: print(f"Cancelling and preparing for channel {channel}")
        return self.pcr_tx(bytes([0x11, channel, data]))

    def ext_info(self, channel:int) -> bytes:
        """
        Sends in a command to the tuner to report program information at full char length.
        This is known as "extended" channel info.
        The response output might look mangled. Currently figuring out why that is.

        Example:
            To check the ext status of channel number 1, the radio will be provided with "22 01".
            Report ext program status for channel 1.

        Args:
            channel (int): The channel value.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if channel not in range(256):
            print("Invalid channel value")
            return b""
        if self.verbose: print(f"Check RX for extinfo on {channel}")
        # I set title size to 0x24 earlier to see if this fixes out the botched output.
        return self.pcr_tx(bytes([0x22, channel]))

    def get_radioid(self) -> bytes:
        """
        Sends in a command to the tuner to report its radio ID.
        Supported radio IDs are 8-char alphanumeric (Excluding letters I, O, S, F).

        Example:
            The radio will be provided with "31".

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.verbose: print("Check RX for ID")
        return self.pcr_tx(bytes([0x31]))

    def firm_ver(self, magic:int=5) -> bytes:
        """
        Sends in a command to the tuner to report its firmware version info and build dates.
        First two bytes of response correspond to an unknown component.
        This is followed by CMB and RX.

        Example:
            The radio will be provided with "70 05".

        Args:
            magic (int, optional): Magic value; all known instances just leave it at 5 so it's defaulted to 5.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.verbose: print("Check RX for radio firmware version")
        return self.pcr_tx(bytes([0x70, magic]))

    def signal_info(self) -> bytes:
        """
        Sends in a command to the tuner to report "extended" signal quality info.

        Example:
            The radio will be provided with "43".

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.verbose: print("Check RX for signal info")
        # It's known that 42 is monitor, but these two are
        # the only ones documented. idk if theres a 41 or 40...
        return self.pcr_tx(bytes([0x43]))

    def chan_mon(self, channel:int, serv_mon:bool=True, prgtype_mon:bool=True, inf_mon:bool=True, ext_mon:bool=True) -> bytes:
        """
        Sends in a command to the tuner to monitor and periodically report information for the given channel number.

        Example:
            To monitor all channel 1 info, the radio will be provided with "50 01 01 01 01 01".
            Turn on monitoring for channel 1, monitor service ID, prog type, info, and extended.

        Args:
            channel (int): The channel value.
            serv_mon (bool, optional): Monitor changes to the channel's service ID. Default is true.
            prgtype_mon (bool, optional): Monitor changes to the channel's program type. Default is true.
            inf_mon (bool, optional): Monitor changes in the program info for the channel. Default is true.
            ext_mon (bool, optional): Monitor changes in the extended program info for the channel. Default is true.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if channel not in range(256):
            print("Invalid channel value")
            return b""
        if self.verbose: print(f"Asking radio to monitor channel {channel}")
        return self.pcr_tx(bytes([0x50, channel, serv_mon, prgtype_mon, inf_mon, ext_mon]))

    def signal_mon(self, toggle:bool) -> bytes:
        """
        Sends in a command to the tuner to monitor and periodically report signal strength.
        Responses are the same as what you get after sending in 43 hex, but without first two status bytes and C:N info.
        This was not a community-documented command.

        Example:
            To enable signal monitoring, the radio will be provided with "42 01".
            Turn on signal monitoring.

        Args:
            toggle (bool): Prompt to enable or disable monitoring.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.verbose: print(f"Asking radio to {'' if toggle else 'not '}monitor signal status")
        return self.pcr_tx(bytes([0x42, toggle]))

    def diag_mon(self, toggle:bool) -> bytes:
        """
        Sends in a command to the tuner to what looks like some diagnostics information.
        Will have to check again later what the responses mean.
        This was not a community-documented command.

        Example:
            To enable diagnostics monitoring, the radio will be provided with "60 01".
            Turn on diagnostics monitoring.

        Args:
            toggle (bool): Prompt to enable or disable monitoring.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.verbose: print(f"Asking radio to {'' if toggle else 'not '}monitor extra info")
        # F0 returned when command is acknowledged.
        # Messages will be received periodically as F1, followed by the info.
        # Would 63 designate to return this info ad-hoc? Who knows!
        return self.pcr_tx(bytes([0x60, toggle]))

    def set_mute(self, mute:bool) -> bytes:
        """
        Sends in a command to the tuner to mute or unmute the DAC.

        Example:
            To mute audio, the radio will be provided with "13 01".
            Mute the audio.

        Args:
            mute (bool): Prompt to mute or unmute audio.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        print(f"{'' if mute else 'Un-'}Muting Audio")
        return self.pcr_tx(bytes([0x13, mute]))

    def wx_datachan(self, sid:int, datflagone:bool=False, datflagtwo:bool=False) -> bytes:
        """
        Sets the specialized receiver to a data channel.
        This command will only work with WX receivers!

        Example:
            By default, if tuning to SID 240, the radio will be provided with
            "4A 10 F0 00 00" to prepare and begin data download.

        Args:
            sid (int): Service ID of the data channel.
            datflagone (bool, optional): Magic flag. Only ever seen enabled if SID is FF (255). Default to false.
            datflagtwo (bool, optional): Magic flag. Only ever seen enabled if SID is FF (255). Default to false.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if sid not in range(256):
            print("Invalid channel value")
            return b""
        if self.verbose: print(f"WX - Preparing for SID {sid}")
        return self.pcr_tx(bytes([0x4A, 0x10, sid, datflagone, datflagtwo]))

    def wx_ping(self) -> bytes:
        """
        Sends a "ping" for the radio to answer back.
        A response of CA 43 hex is expected.
        This command will only work with WX receivers!

        Example:
            The radio will be provided with "4A 43".

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        print("WX - Ping")
        return self.pcr_tx(bytes([0x4A, 0x43]))

    def wx_firmver(self) -> bytes:
        """
        Prompts the radio to report data receiver firmware version.
        This command will only work with WX receivers!

        Example:
            The radio will be provided with "4A 44".

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.verbose: print("WX - Check RX for data receiver version")
        return self.pcr_tx(bytes([0x4A, 0x44]))
    
    def wr_gpsconn(self, toggle:bool) -> bytes:
        """
        Prompts the radio to set the GPS receiver module state if equipped.
        This command will only work with later weather receivers!
        No idea what the radio would return either!

        Example:
            If "toggle" is True, the radio will be provided with
            "4B 09 00 01" to enable its embedded GPS module. If False,
            the last byte sent is "03" to disconnect the module.

        Args:
            toggle (bool): Prompt to enable or disable radio's GPS module.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.verbose: print("WR - Check RX for GPS module confirmation")
        return self.pcr_tx(bytes([0x4B, 0x09, 0x00, 0x01 if toggle else 0x03]))

    def clock_mon(self, toggle:bool) -> bytes:
        """
        Prompts the radio to report the time as synced with the service.

        Example:
            If "toggle" is True, the radio will be provided with
            "4E 01" to enable the clock.

        Args:
            toggle (bool): Prompt to enable or disable time reports.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.verbose: print(f"Turning {'on' if toggle else 'off'} the clock")
        return self.pcr_tx(bytes([0x4E, toggle]))
    
    def direct_enable(self):
        """
        For use with Direct tuners.
        A series of necessary are sent for allowing compatible operation.
        This sets the Direct to enable listening mode, voltage, and unmute the DAC.
        """
        # There's also hint at 74 0D,
        # no idea what 0D does at the moment,
        # assuming this sequence works regardless

        print("Direct listening mode")
        self.pcr_tx(bytes([0x74, 0x00, 0x01]))
        time.sleep(1)  # These sleeps should be event driven instead

        print("Direct voltage on")
        self.pcr_tx(bytes([0x74, 0x02, 0x01, 0x01]))
        time.sleep(1)

        # RX might not be received when unmuting,
        # Let the function finish as-is after this
        print("Direct unmute DAC")
        self.pcr_tx(bytes([0x74, 0x0B, 0x00]))

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
        except:
            print("No serial port in use")
            self.serial_conn = None

    def close(self):
        """
        Close the connection to the serial device.
        """
        if self.serial_conn is None:
            print("No serial port in use")
            return
        self.serial_conn.close()

    def crash_override(self) -> bytes:
        """
        Manually enter payload for debugging purposes.
        Hack the planet!

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        # FOR DEBUG USE
        print("Careful now!")
        print("You're sending commands directly!")
        return self.pcr_tx(
            bytes.fromhex(
                input("Enter payload: ").strip().lower().replace("0x", "").replace(" ", "")
            )
        )

def debug():
    """
    A very simple CaniPy setup.
    Used for debugging purposes.
    Ideally used in environments without a graphical shell.
    """

    # Default to PCR
    baud_rate = 9600
    is_direct = False

    print("=Supported Devices=")
    print("1. PCR")
    print("2. Direct/Commander")
    print("3. WX")
    print("4. WX (Certified)")
    print("0. Exit")

    while True:
        match input("Select device: "):
            case "1":
                break
            case "2":
                is_direct = True
                break
            case "3":
                baud_rate = 38400
                break
            case "4":
                baud_rate = 115200
                break
            case "0":
                return
        print("Invalid option")

    # COM3 used for this test, change if necessary
    pcr_control = CaniPy(port="COM3", baud=baud_rate)

    if is_direct: pcr_control.direct_enable()

    print("=Debug Menu=")
    print("1. Power on")
    print("2. Power off")
    print("3. Tune channel")
    print("4. Fetch channel info")
    print("5. Fetch radio ID")
    print("6. Fetch signal info")
    print("7. Enter manual command")
    print("8. Toggle verbose output")
    print("0. Exit")

    while True:
        match input("Select option: "):
            case "1":
                pcr_control.power_up()
                continue
            case "2":
                pcr_control.power_down()
                continue
            case "3":
                pcr_control.change_channel(input("Channel #: "))
                continue
            case "4":
                pcr_control.channel_info(input("Channel #: "))
                continue
            case "5":
                pcr_control.get_radioid()
                continue
            case "6":
                pcr_control.signal_info()
                continue
            case "7":
                pcr_control.crash_override()
                continue
            case "8":
                pcr_control.verbose = not pcr_control.verbose
                print(f"Verbose output set to {pcr_control.verbose}")
                continue
            case "0":
                break
        print("Invalid option")

    pcr_control.close()

if __name__ == "__main__":
    debug()
