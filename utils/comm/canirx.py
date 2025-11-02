from datetime import datetime, timezone

class CaniRX:
    """
    Functions related to receipt of responses.

    Attributes:
        parent (CaniPy): A main CaniPy instance that this script will support.
    """
    def __init__(self, parent:"CaniPy"):
        self.parent = parent

    @staticmethod
    def fetch_status(payload:bytes) -> str:
        """
        Takes in a payload to intepret its diagnostic
        message into a human-legible response.

        Example:
            If the payload has "01 00" as the status,
            this is an "OK" message, meaning all is good.

        Args:
            payload (bytes): The data to parse the status from.

        Returns:
            status_str: Message corresponding to notice code.
        """
        status_str = ""
        match payload[1]:
            case 0x01:
                if payload[2] == 0x00:
                    status_str += "OK"
                else:
                    status_str += "Normal status"
            case 0x02:
                match payload[2]:
                    case 0x01:
                        # Data is of unidentified type?
                        # Common to see this with overlay channels,
                        # so prompt user that ch is overlay only.
                        status_str += "Channel requires Overlay receiver"
                    case 0x02:
                        # Not exactly sure what this is yet.
                        # Maybe to indicate a data service?
                        status_str += "Channel is a data service"
                    case 0x03:
                        # 02 03 indicates entitled data product
                        status_str += "Data stream available"
                    case 0x04:
                        # 02 04 typically when fetching info on a data channel
                        status_str += "Function unavailable for data channel"
                    case 0x06:
                        status_str += "Irregular power state"
                    case 0x12:
                        status_str += "Extended info only fetched when tuner is active!\n"
                        status_str += "Tune to a channel first before checking info"
                    case _:
                        status_str += "Radio alert"
            case 0x03:
                # Subscriber entitlement alert
                status_str += "Not subscribed"
                if payload[2] == 0x09:
                    status_str += "\nContact service provider to subscribe"
                if payload[2] == 0x0A:
                    status_str += "\nNot available for current subscription"
            case 0x04:
                match payload[2]:
                    case 0x0E:
                        status_str += "Tuner will provide radio ID"
                    case 0x10:
                        status_str += "No signal\n"
                        status_str += "Check if antenna is connected and has a clear view of the sky"
                    case _:
                        status_str += "Tuning alert"
            case 0x06:
                if payload[2] == 0x0B:
                    status_str += "An error occurred when fetching activation info\n"
                    status_str += "Please restart radio or contact the service provider to refresh"
                else:
                    status_str += "Activation alert"
            case 0x07:
                match payload[2]:
                    case 0x0C:
                        # 07 0C, notably when attempting to fetch ext info for ch0
                        status_str += "Command is not supported for this channel"
                    case 0x10:
                        # 07 10, sending commands to a radio tuner that is not on yet
                        status_str += "Please power up the tuner before sending commands"
                    case _:
                        status_str += "Command alert"
            case _:
                status_str += f"Radio reported alert {payload[1]:02X} {payload[2]:02X}"
        return status_str

    def parse_startup(self, payload:bytes):
        """
        Takes in a power-on event response (80 hex) to print out relevant information.
        At this time, verification of the command is by checking if it contains 27 bytes.

        Args:
            payload (bytes): A response, comprised as a set of bytes, to parse the information from.
        """
        if len(payload) == 27:
            self.parent.radio_id = payload[19:27].decode('utf-8')
            self.parent.logprint("===Radio Info===")
            if payload[1]:
                act_status = "N/A"
                if payload[1] == 0x01:
                    act_status = "Yes"
                elif payload[1] == 0x03:
                    act_status = "No"
                else:
                    self.parent.warnprint(self.fetch_status(payload))
                self.parent.logprint(f"Activated: {act_status}")
            # No idea what payload[3] might be yet, always 0 in pcaps.
            # Could be to indicate we're starting at ch0??
            # Ignoring it for now.
            if self.parent.verbose:
                self.parent.logprint(f"RX Version: {payload[4]:X}")
                self.parent.logprint(f"RX Date: {payload[5]:02X}/{payload[6]:02X}/{payload[7]:02X}{payload[8]:02X}")
                self.parent.logprint(f"Last SID 1: {payload[9]:02X}{' (Data)' if payload[10] else ''}")
                self.parent.logprint(f"Last SID 2: {payload[11]:02X}{' (Data)' if payload[12] else ''}")
                self.parent.logprint(f"CBM Version: {payload[13]:X}")
                self.parent.logprint(f"CBM Date: {payload[14]:02X}/{payload[15]:02X}/{payload[16]:02X}{payload[17]:02X}")
            self.parent.logprint(f"Radio ID: {payload[19:27].decode('utf-8')}")
            self.parent.logprint("================")
            return
        self.parent.logprint("Payload not of correct length")
        if self.parent.verbose:
            self.parent.logprint(f"Exp 27, got {len(payload)}")

    def parse_extinfo(self, payload:bytes):
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
            self.parent.logprint("===Title  Info.===")
            self.parent.logprint(f"Channel {payload[3]}")
            if payload[1] != 0x01:
                self.parent.warnprint(self.fetch_status(payload))
                self.parent.logprint("==================")
                return
            if payload[4] == 0x01:
                if payload[3] == self.parent.ch_num:
                    self.parent.artist_name = payload[5:37].decode('utf-8').rstrip(chr(0))
                self.parent.logprint(payload[5:37].decode('utf-8').rstrip(chr(0)))
                if self.parent.verbose:
                    self.parent.logprint(' '.join(f'{b:02X}' for b in payload[37:41]))
            if payload[41] == 0x01:
                if payload[3] == self.parent.ch_num:
                    self.parent.title_name = payload[42:74].decode('utf-8').rstrip(chr(0))
                self.parent.logprint(payload[42:74].decode('utf-8').rstrip(chr(0)))
                if self.parent.verbose:
                    self.parent.logprint(' '.join(f'{b:02X}' for b in payload[74:]))
            self.parent.logprint("==================")
            return
        self.parent.logprint("Payload not of correct length")
        if self.parent.verbose:
            self.parent.logprint(f"Exp 78, got {len(payload)}")

    def parse_chan(self, payload:bytes):
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
            if payload[3] == self.parent.ch_num or payload[4] == self.parent.ch_sid:
                # If number or SID match, we're in this channel.
                # Store values again to ensure they're up to speed.
                is_currchan = True
                self.parent.ch_num = payload[3]
                self.parent.ch_sid = payload[4]
            self.parent.logprint("===Channel Info===")
            self.parent.logprint(f"Channel {payload[3]}")
            if self.parent.verbose:
                self.parent.logprint(f"SID {payload[4]:02X}")
            if payload[1] != 0x01:
                self.parent.warnprint(self.fetch_status(payload))
                self.parent.logprint("==================")
                return
            if payload[5] == 0x01:
                if is_currchan:
                    self.parent.ch_name = payload[6:22].decode('utf-8')
                self.parent.logprint(payload[6:22].decode('utf-8'))
            if payload[40] == 0x01:
                if is_currchan:
                    self.parent.artist_name = payload[41:57].decode('utf-8')
                    self.parent.title_name = payload[57:73].decode('utf-8')
                self.parent.logprint(payload[41:57].decode('utf-8'))
                self.parent.logprint(payload[57:73].decode('utf-8'))
            if payload[22] == 0x01:
                if is_currchan:
                    self.parent.cat_name = payload[24:40].decode('utf-8')
                    self.parent.cat_id = payload[23]
                self.parent.logprint(payload[24:40].decode('utf-8'))
                if self.parent.verbose:
                    self.parent.logprint(f"Cat ID: {payload[23]:02X}")
            self.parent.logprint("==================")
            return
        self.parent.logprint("Payload not of correct length")
        if self.parent.verbose:
            self.parent.logprint(f"Exp 77, got {len(payload)}")

    def parse_sig(self, payload:bytes):
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
            self.parent.sig_strength = payload[3]
            self.parent.ant_strength = payload[4]
            self.parent.ter_strength = payload[5]
            # label dicts
            siglabel = {0x00:"None",0x01:"Fair",0x02:"Good",0x03:"Excellent"}
            antlabel = {0x00:"Disconnected",0x03:"Connected"}
            self.parent.logprint("===Receiver===")
            self.parent.logprint(f"Sat: {siglabel.get(payload[3],f'?({payload[3]})')}")
            self.parent.logprint(f"Ant: {antlabel.get(payload[4],f'?({payload[4]})')}")
            self.parent.logprint(f"Ter: {siglabel.get(payload[5],f'?({payload[5]})')}")
            if self.parent.verbose:
                # Additional info for rock & roll signal, plus terrestrial
                self.parent.logprint("===QPSK/MCM===")
                # Demod lock
                self.parent.logprint(f"Sat1: {'Locked' if payload[6] else 'Lost'}")
                self.parent.logprint(f"Sat2: {'Locked' if payload[7] else 'Lost'}")
                self.parent.logprint(f"Terr: {'Locked' if payload[8] else 'Lost'}")
                self.parent.logprint("=====TDM!=====")
                # TDM lock
                self.parent.logprint(f"Sat1: {'Locked' if payload[9] else 'Lost'}")
                self.parent.logprint(f"Sat2: {'Locked' if payload[10] else 'Lost'}")
                self.parent.logprint(f"Terr: {'Locked' if payload[11] else 'Lost'}")
                self.parent.logprint("=====BER!=====")
                # Bit error rate is two bytes big,
                # 68ths, not exceeding 100%
                self.parent.logprint(f"Sat1: {min(((payload[12] << 8) | payload[13]) / 68, 100):.2f}%")
                self.parent.logprint(f"Sat2: {min(((payload[14] << 8) | payload[15]) / 68, 100):.2f}%")
                self.parent.logprint(f"Terr: {min(((payload[16] << 8) | payload[17]) / 68, 100):.2f}%")
                self.parent.logprint("=====AGC!=====")
                self.parent.logprint(f"Sat: {payload[22]}")
                self.parent.logprint(f"Ter: {payload[23]}")
                if payload[0] == 0xC3:
                    self.parent.logprint("======CN======")
                    # Signal to noise ratio is stored in 1/4 dB
                    self.parent.logprint(f"Sat1: {payload[24]/4}")
                    self.parent.logprint(f"Sat2: {payload[25]/4}")
            self.parent.logprint("==============")
            return
        self.parent.logprint("Payload not of correct length")
        if self.parent.verbose:
            self.parent.logprint(f"Exp 22 or 26, got {len(payload)}")

    def parse_clock(self, payload:bytes, miltime:bool=False):
        """
        Takes in a date-time info response (DF hex) to print and store relevant info.
        Service stamp is reported in coordinated universal time (UTC).
        At this time, verification of the command is by checking if it contains 19 bytes.

        Args:
            payload (bytes): A response, comprised as a set of bytes, to parse the information from.
            miltime (bool, optional): Report the time in 24-hour format. Default to false.
        """
        if len(payload) == 11:
            # Eventually move to primarily using this
            self.parent.sat_datetime = datetime(
                (payload[1]*100)+payload[2],
                payload[3],
                (payload[4] & 0x0F) + (16 if (payload[4]>>4) % 2 else 0),
                payload[5],
                payload[6],
                payload[7] & 0x7F,
                tzinfo=timezone.utc
            )
            # TODO: The heck is with these toggled MSBs in seconds and cycle??
            # This is a semi-long-term analysis!
            weekdaylabel = {
                0x02:"Monday",
                0x04:"Tuesday",
                0x06:"Wednesday",
                0x08:"Thursday",
                0x0A:"Friday",
                0x0C:"Saturday",
                0x0E:"Sunday"
            }
            self.parent.logprint("===  DateTime  ===")
            # Weekday
            self.parent.logprint(
                f"{weekdaylabel.get((payload[4]>>4) - ((payload[4]>>4) % 2),f'?({payload[4]})')}"
            )
            # Date
            self.parent.logprint(
                f"{payload[1]:02d}{payload[2]:02d}-"
                f"{payload[3]:02d}-"
                f"{((payload[4] & 0x0F) + (16 if (payload[4]>>4) % 2 else 0)):02d}"
            )
            # Time
            self.parent.logprint(
                f"{(((payload[5] % 12) or 12) if not miltime else payload[5]):02d}:"
                f"{payload[6]:02d}:"
                f"{(payload[7] & 0x7F):02d}"
                f"{(' PM' if payload[5] >= 12 else ' AM') if not miltime else ''} UTC"
            )
            # I'll need to do more testing before this goes to primetime...
            #print(f"Daylight savings {'' if payload[7] & 0x80 else 'not '}in effect")
            if self.parent.verbose:
                self.parent.logprint(f"Datetime stored: {self.parent.sat_datetime}")
                self.parent.logprint(
                    f"TPS: "
                    f"{self.parent.thread.calc_delta():.2f}"
                )
                # Tick maxes out at 0xFC before rollover gets counted.
                # Day maxes out at 3 1F FC. All tick resets to 0 by midnight.
                # Could be usable to append to datetime for RNG seed, i guess..
                # TODO: Implement a "lucky number" feature for fun
                self.parent.logprint(f"Tick {payload[10]:02X}, rolled over {payload[9]} time(s)")
                self.parent.logprint(
                    f"Day cycle {payload[8]+1 & 0x7F} of 4, "
                    f"hi bit {'on' if payload[8] & 0x80 else 'off'}"
                )
                # Seconds & cycle have high bit on for some reason...
                # Could either of these be daylight savings??
                self.parent.logprint(
                    f"Raw seconds, cycle: "
                    f"{payload[7]:02X} "
                    f"{payload[8]:02X}"
                )
            self.parent.logprint("==================")
            return
        self.parent.logprint("Payload not of correct length")
        if self.parent.verbose:
            self.parent.logprint(f"Exp 11, got {len(payload)}")

    def parse_firminf(self, payload:bytes):
        """
        Takes in a firmware stack info response (E3 hex) to print out its information.
        At this time, verification of the command is by checking if it contains 19 bytes.

        Args:
            payload (bytes): A response, comprised as a set of bytes, to parse the information from.
        """
        if len(payload) == 19:
            self.parent.logprint("===FirmwareInfo===")
            # TODO: Versioning will need to be examined again.
            # I don't have the PCR with me at the moment...
            # For now, I believe this is close enough
            self.parent.logprint(f"HW Version: {payload[3]:X}")
            self.parent.logprint(f"SDEC Version: {payload[4]:X}")
            self.parent.logprint(f"SDEC Date: {payload[5]:02X}/{payload[6]:02X}/{payload[7]:02X}{payload[8]:02X}")
            self.parent.logprint(f"CBM Version: {payload[9]:X}")
            self.parent.logprint(f"CBM Date: {payload[10]:02X}/{payload[11]:02X}/{payload[12]:02X}{payload[13]:02X}")
            self.parent.logprint(f"RX Version: {payload[14]:X}")
            self.parent.logprint(f"RX Date: {payload[15]:02X}/{payload[16]:02X}/{payload[17]:02X}{payload[18]:02X}")
            self.parent.logprint("==================")
            return
        self.parent.logprint("Payload not of correct length")
        if self.parent.verbose:
            self.parent.logprint(f"Exp 19, got {len(payload)}")
