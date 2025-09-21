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

        # Assume radios start at 0
        self.channel = 0

        self.mute = lambda: self.set_mute(True)
        self.unmute = lambda: self.set_mute(False)

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
            # payload[2] and/or payload[3] might correspond
            # to subscribed tier and other status messages
            if self.verbose:
                print(f"RX Version: {'.'.join(list(str(payload[4])))}")
                print(f"RX Date: {payload[5]:02X}/{payload[6]:02X}/{payload[7]:02X}{payload[8]:02X}")
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
        if len(payload) == 26:
            sigstrength = {0x00:"None",0x01:"Fair",0x02:"Good",0x03:"Excellent"}
            antstrength = {0x00:"Disconnected",0x03:"Connected"}
            print("===Receiver===")
            print(f"Sat: {sigstrength.get(payload[3],f'?({payload[3]})')}")
            print(f"Ant: {antstrength.get(payload[4],f'?({payload[4]})')}")
            print(f"Ter: {sigstrength.get(payload[5],f'?({payload[5]})')}")
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
                print(f"Sat1: {payload[12]} {payload[13]}")
                print(f"Sat2: {payload[14]} {payload[15]}")
                print(f"Terr: {payload[16]} {payload[17]}")
                print("=====AGC!=====")
                print(f"Sat: {payload[22]}")
                print(f"Ter: {payload[23]}")
                print("======CN======")
                print(f"Sat1: {payload[24]}")
                print(f"Sat2: {payload[25]}")
            print("==============")
        else:
            print("Payload not of correct length")
            if self.verbose: print(f"Exp 26, got {len(payload)}")

    def power_up(self, ch_lbl:int=16, cat_lbl:int=16, title_lbl:int=24, loss_exp:bool=True) -> bytes:
        print("Powering up")
        return self.pcr_tx(bytes([0x00, ch_lbl, cat_lbl, title_lbl, loss_exp]))

    def power_down(self, pwr_sav:bool=False) -> bytes:
        print("Powering down")
        return self.pcr_tx(bytes([0x01, pwr_sav]))

    def change_channel(self, channel:int, data:bool=False, info_flag:bool=False) -> bytes:
        if channel not in range(256):
            print("Invalid channel value")
            return
        print(f"Changing to channel {channel}{' (Data)' if data else ''}")
        self.channel = channel
        # Some data (i.e. channel 240/F0) is tuned with 01 00 02 instead of 00 00 01.
        # Could be to indicate info? Or the actual control track for subscriber
        # check? Other data tracks tune without this, but implemented anyway as
        # "info_flag" here and in channel_status.
        return self.pcr_tx(bytes([0x10, 0x02 - data, channel, info_flag, 0x00, 0x01 + info_flag]))

    def channel_info(self, channel:int) -> bytes:
        if channel not in range(256):
            print("Invalid channel value")
            return
        if self.verbose: print(f"Check RX for info on {channel}")
        return self.pcr_tx(bytes([0x25, 0x08, channel, 0x00]))

    def channel_status(self, channel:int, info_flag:bool=False) -> bytes:
        if channel not in range(256):
            print("Invalid channel value")
            return
        if self.verbose: print(f"Check RX for status of {channel}")
        # For checking if channel exists
        # Will tune out of currently listening channel!
        return self.pcr_tx(bytes([0x11, channel, info_flag]))

    def audio_info(self, channel:int) -> bytes:
        # AKA "Extended" info; returns full artist+title info of playing content
        # Output tends to be botched during testing, not sure why
        if channel not in range(256):
            print("Invalid channel value")
            return
        if self.verbose: print(f"Check RX for extinfo on {channel}")
        return self.pcr_tx(bytes([0x22, channel]))

    def radio_id(self) -> bytes:
        if self.verbose: print("Check RX for ID")
        return self.pcr_tx(bytes([0x31]))

    def signal_info(self) -> bytes:
        if self.verbose: print("Check RX for signal info")
        return self.pcr_tx(bytes([0x43]))

    def set_mute(self, mute:bool) -> bytes:
        print(f"{'' if mute else 'Un-'}Muting Audio")
        return self.pcr_tx(bytes([0x13, mute]))

    def wx_ping(self) -> bytes:
        # Response of CA 43 expected
        # 4A/CA cmds are WX exclusive!
        print("WX Ping")
        return self.pcr_tx(bytes([0x4A, 0x43]))

    def wx_firmver(self) -> bytes:
        # 4A/CA cmds are WX exclusive!
        if self.verbose: print("Check RX for firmware version")
        return self.pcr_tx(bytes([0x4A, 0x44]))

    # TODO: Eventually implement handling of RX.
    # main.py implements event-driven RX using a
    # discrete thread, reading size from header
    # to distinguish valid command.
    #
    # Main code checks if it received at least 5 bytes:
    # Header, length, & at least 1 byte content.
    #
    # Commands here are sent blind at this stage
    # and rely on RX to check what gets sent in.

    # Kept here for reference, but is event driven
    # So it's left unimplemented until handled
    # Also gotta figure out how to then stop monitoring
    # def monitor_channel(self, channel, serv_mon:bool=False, prgtype_mon:bool=False, inf_mon:bool=False, ext_mon:bool=False) -> bytes:
    #     print("Monitoring channel")
    #     return self.pcr_tx(bytes([0x50, channel, serv_mon, prgtype_mon, inf_mon, ext_mon]))
    
    def direct_enable(self):
        # 74 cmds are exclusive to Direct!
        print("Direct listening mode")
        self.pcr_tx(bytes([0x74, 0x00, 0x01]))
        # These sleeps should be event driven instead
        time.sleep(1)

        print("Direct voltage on")
        self.pcr_tx(bytes([0x74, 0x02, 0x01, 0x01]))
        time.sleep(1)

        # No response would be received here
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
