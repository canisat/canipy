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
    def print_status(payload:bytes):
        """
        Takes in a payload to intepret its diagnostic
        message into a human-legible response.

        Example:
            If the payload has "01 00" as the status,
            this is an "OK" message, meaning all is good.

        Args:
            payload (bytes): The data to parse the status from.
        """
        match payload[1]:
            case 0x01:
                if payload[2] == 0x00:
                    print("OK")
                else:
                    print("Normal status")
            case 0x02:
                match payload[2]:
                    case 0x01:
                        # Data is of unidentified type?
                        # Common to see this with overlay channels,
                        # so prompt user that ch is overlay only.
                        print("Channel requires Overlay receiver")
                    case 0x02:
                        # Not exactly sure what this is yet.
                        # Maybe to indicate a data service?
                        print("Channel is a data service")
                    case 0x03:
                        # 02 03 indicates entitled data product
                        print("Data stream available")
                    case 0x04:
                        print("Tuner not on correct mode for channel")
                    case 0x06:
                        print("Irregular power state")
                    case 0x12:
                        print("Extended info only fetched when tuner is active!")
                        print("Tune to a channel first before checking info")
                    case _:
                        print("Radio alert")
            case 0x03:
                # Subscriber entitlement alert
                print("Not subscribed")
                if payload[2] == 0x09:
                    print("Contact service provider to subscribe")
                if payload[2] == 0x0a:
                    print("Not available for current subscription")
            case 0x04:
                match payload[2]:
                    case 0x0E:
                        print("Echo radio information")
                    case 0x10:
                        print("No signal")
                        print("Check if antenna is connected and has a clear view of the sky")
                    case _:
                        print("Tuning alert")
            case 0x07:
                if payload[2] == 0x10:
                    # 07 10, sending commands to a radio tuner that is not on yet
                    print("Please power up the tuner before sending commands")
                else:
                    print("Command alert")
            case _:
                print(f"Radio reported alert {payload[1]:02X} {payload[2]:02X}")

    def parse_startup(self, payload:bytes):
        """
        Takes in a power-on event response (80 hex) to print out relevant information.
        At this time, verification of the command is by checking if it contains 27 bytes.

        Args:
            payload (bytes): A response, comprised as a set of bytes, to parse the information from.
        """
        if len(payload) == 27:
            self.parent.radio_id = payload[19:27].decode('utf-8')
            print("===Radio Info===")
            if payload[1]:
                print(f"Activated: {'No' if payload[1] == 0x03 else 'Yes'}")
            # No idea what payload[3] might be yet, always 0 in pcaps.
            # Could be to indicate we're starting at ch0??
            # Ignoring it for now.
            if self.parent.verbose:
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
        if self.parent.verbose: print(f"Exp 27, got {len(payload)}")

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
            print("===Title  Info.===")
            print(f"Channel {payload[3]}")
            if payload[1] != 0x01:
                self.print_status(payload)
                print("==================")
                return
            if payload[4] == 0x01:
                if payload[3] == self.parent.ch_num:
                    self.parent.artist_name = payload[5:37].decode('utf-8').rstrip(chr(0))
                print(payload[5:37].decode('utf-8').rstrip(chr(0)))
                if self.parent.verbose: print(' '.join(f'{b:02X}' for b in payload[37:41]))
            if payload[41] == 0x01:
                if payload[3] == self.parent.ch_num:
                    self.parent.title_name = payload[57:73].decode('utf-8').rstrip(chr(0))
                print(payload[42:74].decode('utf-8').rstrip(chr(0)))
                if self.parent.verbose: print(' '.join(f'{b:02X}' for b in payload[74:]))
            print("==================")
            return
        print("Payload not of correct length")
        if self.parent.verbose: print(f"Exp 78, got {len(payload)}")

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
            if (payload[1], payload[2]) == (0x04, 0x0E):
                if payload[5] != 0x01:
                    # Channel 0 contains radio info,
                    # unless radio already cached ch info.
                    # Structure to the size of a startup RX.
                    self.parse_startup(
                        bytes(
                            bytes(4) +
                            payload[6:13] +
                            bytes(2) +
                            payload[13:18] +
                            bytes([0x08]) +
                            payload[18:26]
                        )
                    )
                else:
                    # If station info's cached,
                    # just return radio ID.
                    self.parent.tx.get_radioid()
                return
            print("===Channel Info===")
            print(f"Channel {payload[3]}")
            if self.parent.verbose: print(f"SID {payload[4]:02X}")
            if payload[1] != 0x01:
                self.print_status(payload)
                print("==================")
                return
            if payload[5] == 0x01:
                if is_currchan:
                    self.parent.ch_name = payload[6:22].decode('utf-8')
                print(payload[6:22].decode('utf-8'))
            if payload[40] == 0x01:
                if is_currchan:
                    self.parent.artist_name = payload[41:57].decode('utf-8')
                    self.parent.title_name = payload[57:73].decode('utf-8')
                print(payload[41:57].decode('utf-8'))
                print(payload[57:73].decode('utf-8'))
            if payload[22] == 0x01:
                if is_currchan:
                    self.parent.cat_name = payload[24:40].decode('utf-8')
                    self.parent.cat_id = payload[23]
                print(payload[24:40].decode('utf-8'))
                if self.parent.verbose: print(f"Cat ID: {payload[23]:02X}")
            print("==================")
            return
        print("Payload not of correct length")
        if self.parent.verbose: print(f"Exp 77, got {len(payload)}")

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
            siglabel = {0x00:"None",0x01:"Fair",0x02:"Good",0x03:"Excellent"}
            antlabel = {0x00:"Disconnected",0x03:"Connected"}
            print("===Receiver===")
            print(f"Sat: {siglabel.get(payload[3],f'?({payload[3]})')}")
            print(f"Ant: {antlabel.get(payload[4],f'?({payload[4]})')}")
            print(f"Ter: {siglabel.get(payload[5],f'?({payload[5]})')}")
            if self.parent.verbose:
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
                    # Signal to noise ratio is stored in 1/4 dB
                    print(f"Sat1: {payload[24]/4}")
                    print(f"Sat2: {payload[25]/4}")
            print("==============")
            return
        print("Payload not of correct length")
        if self.parent.verbose: print(f"Exp 22 or 26, got {len(payload)}")

    def parse_clock(self, payload:bytes, miltime:bool=False):
        """
        Takes in a date-time info response (DF hex) to print and store relevant info.
        Service stamp is reported in coordinated universal time (UTC).
        At this time, verification of the command is by checking if it contains 19 bytes.

        Args:
            payload (bytes): A response, comprised as a set of bytes, to parse the information from.
            miltime (bool, optional): Report the time in 24-hour format. Default to false.
        """
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
        if len(payload) == 11:
            print("===  DateTime  ===")
            # Weekday
            print(
                f"{weekdaylabel.get((payload[4]>>4) - ((payload[4]>>4) % 2),f'?({payload[4]})')}"
            )
            # Date
            print(
                f"{payload[1]:02d}{payload[2]:02d}-"
                f"{payload[3]:02d}-"
                f"{((payload[4] & 0x0F) + (16 if (payload[4]>>4) % 2 else 0)):02d}"
            )
            # Time
            print(
                f"{(((payload[5] % 12) or 12) if not miltime else payload[5]):02d}:"
                f"{payload[6]:02d}:"
                f"{(payload[7] & 0x7F):02d}"
                f"{(' PM' if payload[5] >= 12 else ' AM') if not miltime else ''} UTC"
            )
            # I'll need to do more testing before this goes to primetime...
            #print(f"Daylight savings {'' if payload[7] & 0x80 else 'not '}in effect")
            if self.parent.verbose:
                print(f"Datetime stored: {self.parent.sat_datetime}")
                print(
                    f"TPS: "
                    f"{self.parent.thread.calc_delta():.2f}"
                )
                # Tick maxes out at 0xFC before rollover gets counted.
                # Day maxes out at 3 1F FC. All tick resets to 0 by midnight.
                # Could be usable to append to datetime for RNG seed, i guess..
                # TODO: Implement a "lucky number" feature for fun
                print(f"Tick {payload[10]:02X}, rolled over {payload[9]} time(s)")
                print(
                    f"Day cycle {payload[8]+1 & 0x7F} of 4, "
                    f"hi bit {'on' if payload[8] & 0x80 else 'off'}"
                )
                # Seconds & cycle have high bit on for some reason...
                # Could either of these be daylight savings??
                print(
                    f"Raw seconds, cycle: "
                    f"{payload[7]:02X} "
                    f"{payload[8]:02X}"
                )
            print("==================")
            return
        print("Payload not of correct length")
        if self.parent.verbose: print(f"Exp 11, got {len(payload)}")

    def parse_firminf(self, payload:bytes):
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
            print("==================")
            return
        print("Payload not of correct length")
        if self.parent.verbose: print(f"Exp 19, got {len(payload)}")

    def conductor(self, payload:bytes):
        """
        Takes in a response payload to then interpret/display the information stored within it.
        The message type is checked to select how to handle it.

        Args:
            payload (bytes): A response, comprised as a set of bytes, to parse the information from.
        """
        # payload[1] and payload[2] appear to
        # always be status code and detail respectively,
        # except if it's an event driven response.
        match payload[0]:
            case 0x80:
                self.parse_startup(payload)
            case 0x81:
                print("Goodnight")
            case 0x8b:
                print(
                    f"Line level set to "
                    f"{-payload[3] if payload[3] <= 0x60 else payload[3] - 0x60}dB"
                )
            case 0x90:
                if self.parent.verbose: print(f"SID {payload[3]}, Ch. {payload[4]}")
                if payload[5]:
                    # When first tuning to a data channel, like
                    # main WX SID 240, this will still be 0. But tune
                    # normally to another channel after, this becomes 1.
                    # Might be to indicate auxiliary tuning is enabled
                    # to allow simultaneous audio and data tuning.
                    print(f"Data aux is on")
                if (payload[1], payload[2]) not in [(0x01, 0x00), (0x04, 0x0E)]:
                    # Report status if alert, or not ch0
                    self.print_status(payload)
                    return
                self.parent.ch_sid = payload[3]
                self.parent.ch_num = payload[4]
                self.parent.tx.channel_info(payload[4])
            case 0x91:
                # Hacky way to distinguish, but if it's data, it's usually SID
                # Or maybe 11/91 is exclusively sid, im not sure...
                if payload[4]:
                    self.parent.ch_sid = payload[3]
                else:
                    self.parent.ch_num = payload[3]
                print("Current channel tune cancelled! You will be tuned out!")
                if payload[3]:
                    print(f"Ready for channel {payload[3]}{' (Data)' if payload[4] else ''}")
                print("Change channel to resume content")
            case 0x93:
                print(f"Mute: { {0x00:'Off',0x01:'On'}.get(payload[3],f'?({payload[3]})') }")
            case 0xA2:
                self.parse_extinfo(payload)
            case 0xA5:
                self.parse_chan(payload)
            case 0xB1:
                if len(payload) != 12:
                    print("Invalid Radio ID length")
                    if self.parent.verbose: print(f"Exp 12, got {len(payload)}")
                    return
                # if good, print characters
                self.parent.radio_id = payload[4:12].decode('utf-8')
                print(f"Radio ID: {payload[4:12].decode('utf-8')}")
            case 0xC1 | 0xC3:
                self.parse_sig(payload)
            case 0xC2:
                print("Signal strength monitoring status updated")
            case 0xCA:
                # 'A' cmds are WX specific!
                if payload[1] == 0x40:
                    if payload[2] == 0xff:
                        print(f"WX - Error setting up data RX on {payload[4]}")
                        if payload[3] == 0x08:
                            # Not exactly sure if this correct...
                            print("Unable to listen as data")
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
            case 0xCF | 0xD0:
                # Usually 50/D0, but 4F/CF may also be used to
                # achieve the same thing, especially with
                # receivers that are also tuned to data!
                if payload[3]:
                    print(f"Monitoring channel {payload[3]}")
                    return
                print("Channel monitoring stopped")
            case 0xD1:
                if payload[2] == 0x01:
                    # Store only if channel numbers match!
                    if payload[1] == self.parent.ch_num:
                        self.parent.ch_name = payload[3:19].decode('utf-8')
                    print("===Channel Name===")
                    print(f"Channel {payload[1]}")
                    print(payload[3:19].decode('utf-8'))
                    # Trailing bytes, this could be length side effect?
                    # Like with whats happening with extended info?
                    # Treat as debug info for now.
                    if self.parent.verbose:
                        print(' '.join(f'{b:02X}' for b in payload[19:]))
                    print("==================")
            case 0xD2:
                if payload[3] == 0x01:
                    if payload[1] == self.parent.ch_num:
                        self.parent.cat_id = payload[2]
                        self.parent.cat_name = payload[4:].decode('utf-8')
                    print("===Ch. Category===")
                    print(f"Channel {payload[1]}")
                    print(payload[4:].decode('utf-8'))
                    if self.parent.verbose:
                        print(f"Cat ID: {payload[2]:02X}")
                    print("==================")
            case 0xD3:
                if payload[2] == 0x01:
                    if payload[1] == self.parent.ch_num:
                        self.parent.artist_name = payload[3:19].decode('utf-8')
                        self.parent.title_name = payload[19:].decode('utf-8')
                    print("===Program Info===")
                    print(f"Channel {payload[1]}")
                    print(payload[3:19].decode('utf-8'))
                    print(payload[19:].decode('utf-8'))
                    print("==================")
            case 0xD4:
                if payload[2] == 0x01:
                    if payload[1] == self.parent.ch_num:
                        self.parent.artist_name = payload[3:].decode('utf-8').rstrip(chr(0))
                    print("===Artist Info.===")
                    print(f"Channel {payload[1]}")
                    print(payload[3:].decode('utf-8').rstrip(chr(0)))
                    print("==================")
            case 0xD5:
                if payload[2] == 0x01:
                    if payload[1] == self.parent.ch_num:
                        self.parent.title_name = payload[3:].decode('utf-8').rstrip(chr(0))
                    print("===Title  Info.===")
                    print(f"Channel {payload[1]}")
                    print(payload[3:].decode('utf-8').rstrip(chr(0)))
                    print("==================")
            case 0xD6:
                if payload[3] == 0x01 or payload[4] == 0x01:
                    print("===Program Len.===")
                    print(f"Channel {payload[1]}")
                    if self.parent.verbose:
                        print(f"Time Format: {payload[2]:02X}")
                    if payload[3] == 0x01:
                        print(f"Started {round(((payload[5] << 8) | payload[6])/60)}m ago")
                    if payload[4] == 0x01:
                        print(f"Ends in {round(((payload[7] << 8) | payload[8])/60)}m")
                    print("==================")
            case 0xDE:
                print("Clock monitoring status updated")
            case 0xDF:
                self.parse_clock(payload)
            case 0xE0:
                print("Fetched activation info")
            case 0xE1:
                print("Fetched deactivation info")
            case 0xE3:
                self.parse_firminf(payload)
            case 0xE4 | 0xF4:
                # Acknowledgement of Direct responses.
                # nsayer ref listens to E4 though?? differs by 4th opcode
                # TODO: cover both until better understood
                print(f"Direct command Acknowledged ({payload[0]:02X})")
            case 0xEA:
                if payload[1] == 0xD0:
                    # Write data frames
                    self.parent.wx.parse_data(payload, True)
                    return
                print("Data packet received")
            case 0xF0:
                print("Diagnostic info monitoring status updated")
            case 0xF1:
                if self.parent.verbose:
                    # TODO: examine how diag is laid out, appears to be 8 or 9 fields
                    print("=== DIAGNOSTIC ===")
                    print(payload[2:].decode('utf-8'))
                    print("==================")
            case 0xF2:
                # Direct idle frames.
                # Counted, but generally just ignored.
                self.parent.direct_idleframes += 1
            case 0xFF:
                print("Warning! Radio reported an error")
                if (payload[1], payload[2]) == (0x01, 0x00):
                    # 01 00 (aka OK) on error, typically corresponds to antenna
                    print("Antenna not detected, check antenna")
                elif (payload[1], payload[2]) == (0xFF, 0xFF):
                    # If it's all F's, it's something serious!!!
                    # (Likely has a message, print it out!)
                    print(f"{payload[3:].decode('utf-8')}")
                else:
                    self.print_status(payload)
                if self.parent.verbose:
                    print(f"{payload[1]:02X} {payload[2]:02X} {payload[3:].decode('utf-8')}")
                print("Radio may still be operated")
                print("If errors persist, check or power-cycle the radio")
            case _:
                print(f"Unknown return code {hex(payload[0])}")

    def acid_burn(self):
        """
        Manually enter payload for debugging purposes.
        Hack the planet!
        """
        # FOR DEBUG USE
        self.parent.verbose = True
        print("Careful now!")
        print("You're about to send manual commands to the conductor!")
        self.conductor(
            bytes.fromhex(
                input("Enter payload: ").strip().lower().replace("0x", "").replace(" ", "")
            )
        )
        self.parent.verbose = False
