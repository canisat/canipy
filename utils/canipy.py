try:
    import serial
except:
    print("Serial Library not available")

import time

class CaniPy:
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
        self.ter_strength = -1

        self.mute = lambda: self.set_mute(True)
        self.unmute = lambda: self.set_mute(False)

        self.sigmon_enable = lambda: self.signal_mon(True)
        self.sigmon_disable = lambda: self.signal_mon(False)

        # These may be valid
        self.curr_channel_info = lambda: self.pcr_tx(bytes([0x25, 0x08]))
        self.next_channel_info = lambda: self.pcr_tx(bytes([0x25, 0x09]))
        self.prev_channel_info = lambda: self.pcr_tx(bytes([0x25, 0x10]))

        # I think just sending 22 would imply current channel
        self.curr_audio_info = lambda: self.pcr_tx(bytes([0x22]))

        self.set_port = lambda new_port: self.set_serial_params(new_port, self.baud_rate)
        self.set_baud:Callable[[int], None] = lambda new_baud: self.set_serial_params(self.port_name, new_baud)

        self.serial_conn = None
        if port: self.set_serial_params(port, baud)

        print("CaniPy started")

    def pcr_tx(self, payload:bytes) -> bytes:
        if self.serial_conn == None:
            print("No serial port in use")
            return
        length = len(payload).to_bytes(2, byteorder='big')
        command = self.header + length + payload + self.tail
        self.serial_conn.write(command)
        if self.verbose:
            print(f"Sent: {" ".join(f"{b:02X}" for b in payload)}")
        return payload

    def rx_startup(self, payload:bytes):
        if len(payload) == 27:
            print("===Radio Info===")
            print(f"Activated: {'No' if payload[1] == 0x3 else 'Yes'}")
            # No idea what payload[3] might be yet, always 0 in pcaps.
            # Ignoring it for now.
            if self.verbose:
                print(f"RX Version: {'.'.join(list(str(payload[4])))}")
                print(f"RX Date: {payload[5]:02X}/{payload[6]:02X}/{payload[7]:02X}{payload[8]:02X}")
                # In this project, data will be tackled (Eventually).
                print(f"Last SID 1: {payload[9]:02X}{' (Data)' if payload[10] else ''}")
                print(f"Last SID 2: {payload[11]:02X}{' (Data)' if payload[12] else ''}")
                print(f"CMB Version: {'.'.join(list(str(payload[13])))}")
                print(f"CMB Date: {payload[14]:02X}/{payload[15]:02X}/{payload[16]:02X}{payload[17]:02X}")
            print(f"Radio ID: {payload[19:27].decode('utf-8')}")
            print("================")
        else:
            print("Payload not of correct length")
            if self.verbose: print(f"Exp 27, got {len(payload)}")

    def rx_chan(self, payload:bytes):
        if len(payload) == 77:
            print("===Channel Info===")
            print(f"Channel {payload[3]}")
            if payload[1] == 0x03:
                print("Not subscribed")
                if payload[2] == 0x09:
                    print("Contact service provider to subscribe")
            else:
                if payload[5]:
                    print(f"{payload[6:22].decode('utf-8')}")
                if payload[40]:
                    print(f"{payload[41:57].decode('utf-8')}")
                    print(f"{payload[57:73].decode('utf-8')}")
                if payload[22]:
                    print(f"{payload[24:40].decode('utf-8')}")
                    if self.verbose:
                        print(f"Cat ID: {payload[23]:02X}")
                if self.verbose:
                    print(f"Service ID: {payload[4]:02X}")
            print("==================")
        else:
            print("Payload not of correct length")
            if self.verbose: print(f"Exp 77, got {len(payload)}")

    def rx_sig(self, payload:bytes):
        if len(payload) in (22, 26):
            if len(payload) == 22:
                # If C1 event-driven poll, pad it to conform
                payload = payload[:1] + bytes([1,0]) + payload[1:] + bytes(2)
            self.sig_strength = -1 if not payload[4] else payload[3]
            self.ter_strength = -1 if not payload[4] else payload[3]
            siglabel = {0x00:"None",0x01:"Fair",0x02:"Good",0x03:"Excellent"}
            antlabel = {0x00:"Disconnected",0x03:"Connected"}
            print("===Receiver===")
            print(f"Sat: {siglabel.get(payload[3],f'?({payload[3]})')}")
            print(f"Ant: {antlabel.get(payload[4],f'?({payload[4]})')}")
            print(f"Ter: {siglabel.get(payload[5],f'?({payload[5]})')}")
            if self.verbose:
                print("===QPSK/MCM===")
                print(f"Sat1: {payload[6]}")
                print(f"Sat2: {payload[7]}")
                print(f"Terr: {payload[8]}")
                print("=====TDM!=====")
                print(f"Sat1: {payload[9]}")
                print(f"Sat2: {payload[10]}")
                print(f"Terr: {payload[11]}")
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
        else:
            print("Payload not of correct length")
            if self.verbose: print(f"Exp 22 or 26, got {len(payload)}")

    def power_up(self, ch_lbl:int=16, cat_lbl:int=16, title_lbl:int=36, loss_exp:bool=True) -> bytes:
        print("Powering up")
        return self.pcr_tx(bytes([0x00, ch_lbl, cat_lbl, title_lbl, loss_exp]))

    def power_down(self, pwr_sav:bool=False) -> bytes:
        print("Powering down")
        return self.pcr_tx(bytes([0x01, pwr_sav]))

    def change_channel(self, channel:int, is_sid:bool=False, data:bool=False, prg_type:int=0) -> bytes:
        if channel not in range(256):
            print("Invalid channel value")
            return
        print(f"Changing to channel {channel}{' (Data)' if data else ''}")
        if not is_sid: self.ch_num = channel
        # "Some data (i.e. SID 240/F0) is tuned with 01 00 02"
        # THIS SEEMS TO BE THE CASE FOR MOST IF NOT ALL DATA!
        # BUT ONLY ONE WAY TO FIND OUT IF THIS IS 100% TRUE!
        #
        # 02 is for tuning by assigned "virtual" number
        # 01 tunes based on service ID, essentially the raw index
        # 
        # No idea what program type is all about, assume 0
        # for now cus none of the pcaps used it thus far.
        return self.pcr_tx(bytes([0x10, 0x02 - is_sid, channel, data, prg_type, 0x01 + data]))

    def channel_info(self, channel:int, is_sid:bool=False, prg_type:int=0) -> bytes:
        if channel not in range(256):
            print("Invalid channel value")
            return
        if self.verbose: print(f"Check RX for info on {channel}")
        # 07 allows for checking by SID
        return self.pcr_tx(bytes([0x25, 0x08 - is_sid, channel, prg_type]))

    def channel_status(self, channel:int, data:bool=False) -> bytes:
        if channel not in range(256):
            print("Invalid channel value")
            return
        if self.verbose: print(f"Check RX for status of {channel}")
        # For checking if channel exists??
        # Will tune out of currently listening channel!
        # Need to be sure what 11/91 actually does...
        # I really dont know given it's undocumented.
        # Is it SID only? Assigned channe number?
        # I did notice the 3rd byte may be a data flag
        return self.pcr_tx(bytes([0x11, channel, data]))

    def audio_info(self, channel:int) -> bytes:
        # AKA "Extended" info; returns full artist+title info of playing content
        # Output might look botched, i think it was supposed to be set to an
        # expected value. I set title size to 0x24 to see if this fixes it.
        if channel not in range(256):
            print("Invalid channel value")
            return
        if self.verbose: print(f"Check RX for extinfo on {channel}")
        return self.pcr_tx(bytes([0x22, channel]))

    def radio_id(self) -> bytes:
        if self.verbose: print("Check RX for ID")
        return self.pcr_tx(bytes([0x31]))

    def firm_ver(self, magic:int=5) -> bytes:
        # Fetches radio version numbers and dates
        # Not sure what the first two bytes correspond to,
        # then that build date. Followed by CMB and RX versions.
        # Not sure what the other TX byte is for, it's always
        # noted with 5 during testing. Only send 5 for now,
        # override if you dare...
        if self.verbose: print("Check RX for radio firmware version")
        return self.pcr_tx(bytes[0x70, magic])

    def signal_info(self) -> bytes:
        # Sometimes referred as "extended" signal quality.
        # It's known that 42 is monitor, but these two are
        # the only ones documented. idk if theres a 41 or 40...
        if self.verbose: print("Check RX for signal info")
        return self.pcr_tx(bytes([0x43]))

    # TODO: Continue implementation of RX handling.
    # main.py implements event-driven RX using a
    # discrete thread, reading size from header
    # to distinguish valid command.
    #
    # Main code checks if it received at least 5 bytes:
    # Header, length, & at least 1 byte content.
    #
    # This thread code is to be moved as a util script.

    # Kept here for reference, handling will need to be
    # implemented first. Also gotta figure out how to
    # then stop monitoring. I believe this is just setting ch0?
    # def chan_mon(self, channel, serv_mon:bool=False, prgtype_mon:bool=False, inf_mon:bool=False, ext_mon:bool=False) -> bytes:
    #     print("Monitoring channel")
    #     return self.pcr_tx(bytes([0x50, channel, serv_mon, prgtype_mon, inf_mon, ext_mon]))

    def signal_mon(self, toggle:bool) -> bytes:
        if self.verbose: print(f"Asking radio to {'' if toggle else 'not '}monitor signal status")
        return self.pcr_tx(bytes([0x42, toggle]))

    def diag_mon(self, toggle:bool) -> bytes:
        if self.verbose: print(f"Asking radio to {'' if toggle else 'not '}monitor extra info")
        # Sending 60 prompts the radio to send what might be diagnostics info.
        # F0 returned when command is acknowledged.
        # Messages will be received periodically as F1, followed by the info.
        # No idea what this info specifically corresponds to at the moment.
        # Would 63 designate to return this info ad-hoc? Who knows!
        return self.pcr_tx(bytes([0x60, toggle]))

    def set_mute(self, mute:bool) -> bytes:
        print(f"{'' if mute else 'Un-'}Muting Audio")
        return self.pcr_tx(bytes([0x13, mute]))

    def wx_ping(self) -> bytes:
        # Response of CA 43 expected
        # 'A' cmds are WX specific!
        print("WX Ping")
        return self.pcr_tx(bytes([0x4A, 0x43]))

    def wx_firmver(self) -> bytes:
        # 'A' cmds are WX specific!
        if self.verbose: print("Check RX for WX firmware version")
        return self.pcr_tx(bytes([0x4A, 0x44]))
    
    def direct_enable(self):
        # 74 cmds are exclusive to Direct!
        # There's also hint at 74 0D,
        # no idea what 0D does at the moment,
        # assuming this sequence works regardless
        print("Direct listening mode")
        self.pcr_tx(bytes([0x74, 0x00, 0x01]))
        # These sleeps should be event driven instead
        time.sleep(1)

        print("Direct voltage on")
        self.pcr_tx(bytes([0x74, 0x02, 0x01, 0x01]))
        time.sleep(1)

        # RX might not be received when unmuting,
        # Let the function finish as-is after this
        print("Direct unmute DAC")
        self.pcr_tx(bytes([0x74, 0x0B, 0x00]))

    def set_serial_params(self, port, baud:int):
        self.port_name = port
        self.baud_rate = baud
        try:
            self.serial_conn = serial.Serial(port=port, baudrate=baud, timeout=1)
        except:
            print("No serial port in use")
            self.serial_conn = None

    def close(self):
        if self.serial_conn == None:
            print("No serial port in use")
            return
        self.serial_conn.close()

    def crash_override(self) -> bytes:
        # FOR DEBUG USE
        print("Careful now!")
        print("You're sending commands directly!")
        return self.pcr_tx(
            bytes.fromhex(
                input("Enter payload: ").strip().lower().replace("0x", "").replace(" ", "")
            )
        )

def debug():
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
                pcr_control.radio_id()
                continue
            case "6":
                pcr_control.signal_info()
                continue
            case "7":
                pcr_control.crash_override()
                continue
            case "0":
                break
        print("Invalid option")

    pcr_control.close()

if __name__ == "__main__":
    debug()
