import threading

class CaniRX:
    """
    Functions related to receipt of responses.

    Attributes:
        parent (CaniPy): A main CaniPy instance that this script will support.
    """
    # Functions will be moved here gradually
    def __init__(self, parent:"CaniPy"):
        self.parent = parent

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
            print(f"Activated: {'No' if payload[1] == 0x3 else 'Yes'}")
            # No idea what payload[3] might be yet, always 0 in pcaps.
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
            if payload[1] == 0x03:
                print("Not subscribed")
                if payload[2] == 0x09:
                    print("Contact service provider to subscribe")
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
            print("===Channel Info===")
            print(f"Channel {payload[3]}")
            if payload[1] == 0x03:
                print("Not subscribed")
                if payload[2] == 0x09:
                    print("Contact service provider to subscribe")
                print("==================")
                return
            if payload[1] == 0x04:
                if payload[2] == 0x0E:
                    print("End of line-up reached")
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
            if self.parent.verbose: print(f"Service ID: {payload[4]:02X}")
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
            print(
                f"{payload[1]:02d}{payload[2]:02d}-"
                f"{payload[3]:02d}-"
                f"{(payload[4]&0x0F):02d}"
            )
            # Time
            print(
                f"{(((payload[5] % 12) or 12) if not miltime else payload[5]):02d}:"
                f"{payload[6]:02d}:"
                f"{(payload[7] - 0x80 if payload[7] & 0x80 else payload[7]):02d}"
                f"{(' PM' if payload[5] >= 12 else ' AM') if not miltime else ''} UTC"
            )
            if self.parent.verbose:
                # Seconds have high bit on for some reason...
                # TODO: Figure out why this is.
                # For now, AM and PM are determined by 24h time.
                # I thought this was an AM PM indicator at first.
                print(f"Raw seconds due to high bit: {payload[7]:02X}")
                # Tick can be useful for RNG
                # Feed test[8:11] as a seed
                # TODO: Implement "lucky number" feature just for fun
                print(f"Tick is at {payload[10]:02X}, rolled over {payload[9]} times.")
                print(f"Roll-over cleared {payload[8]} times since epoch.")
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
            return
        print("Payload not of correct length")
        if self.parent.verbose: print(f"Exp 19, got {len(payload)}")
