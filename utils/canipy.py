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

        # Assume radios start at 0
        self.channel = 0

        self.mute = lambda: self.set_mute(True)
        self.unmute = lambda: self.set_mute(False)

        self.curr_channel_info = lambda: self.channel_info(self.channel)
        self.curr_audio_info = lambda: self.audio_info(self.channel)

        self.set_port = lambda new_port: self.set_serial_params(new_port, self.baud_rate)
        self.set_baud:Callable[[int], None] = lambda new_baud: self.set_serial_params(self.port_name, new_baud)

        print("CaniPy started")

        self.serial_conn = None
        if port:
            self.set_serial_params(port, baud)

    def pcr_tx(self, payload:bytes) -> bytes:
        if self.serial_conn == None:
            print("No serial port to read")
            return
        length = len(payload).to_bytes(2, byteorder='big')
        command = self.header + length + payload + self.tail
        self.serial_conn.write(command)
        print(f"Sent: {" ".join(f"{b:02X}" for b in payload)}")
        return payload

    def power_up(self, ch_lbl:int=16, cat_lbl:int=16, title_lbl:int=24, loss_exp:bool=True) -> bytes:
        print("Powering up")
        return self.pcr_tx(bytes([0x00, ch_lbl, cat_lbl, title_lbl, loss_exp]))

    def power_down(self, pwr_sav:bool=False) -> bytes:
        print("Powering down")
        return self.pcr_tx(bytes([0x01, pwr_sav]))

    def change_channel(self, channel:int, data:bool=False, info_flag:bool=False) -> bytes:
        if channel not in range(256):
            print(f"Invalid channel value, got {channel}")
            return
        print(f"Changing to channel {channel}{' (Data)' if data else ''}")
        self.channel = channel
        # Some data (i.e. channel 240/F0) is tuned with 01 00 02 instead of 00 00 01.
        # Could be to indicate info? Or the actual control track for subscriber
        # check? Other data tracks tune without this, but implemented anyway as
        # "info_flag" here and in channel_status.
        return self.pcr_tx(bytes([0x10, 0x01 if data else 0x02, channel, info_flag, 0x00, 0x01 + info_flag]))

    def channel_info(self, channel:int) -> bytes:
        # Noting these cus they may still be valid.
        # These cmds are usually reserved for headunits
        # that look ahead/behind the current ch, and
        # when brute listing available channels
        # self.pcr_tx(bytes([0x25, 0x08])) Curr ch
        # self.pcr_tx(bytes([0x25, 0x09])) Next ch
        # self.pcr_tx(bytes([0x25, 0x10])) Prev ch
        if channel not in range(256):
            print("Invalid channel value")
            return
        print(f"Check pcap for info on channel {channel}")
        return self.pcr_tx(bytes([0x25, 0x08, channel, 0x00]))

    def channel_status(self, channel:int, info_flag:bool=False) -> bytes:
        if channel not in range(256):
            print("Invalid channel value")
            return
        print(f"Check pcap for status of channel {channel}")
        # For checking sub status
        # Will tune out of currently listening channel
        return self.pcr_tx(bytes([0x11, channel, info_flag]))

    def audio_info(self, channel:int) -> bytes:
        # AKA "Extended" info; returns full artist+title info of playing content
        # I think just sending 22 would imply current channel
        if channel not in range(256):
            print("Invalid channel value")
            return
        print(f"Check pcap for info on channel {channel}")
        return self.pcr_tx(bytes([0x22, channel]))

    def radio_id(self) -> bytes:
        print("Check pcap for ID")
        return self.pcr_tx(bytes([0x31]))

    def signal_info(self) -> bytes:
        print("Check pcap for signal info")
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
        print("Check pcap for firmware version")
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
    # and rely on pcap to check what gets sent in.

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
            print("No serial port to read")
            self.serial_conn = None

    def close(self):
        if self.serial_conn == None:
            print("No serial port to read")
            return
        self.serial_conn.close()

    def crash_override(self) -> bytes:
        # FOR DEBUG USE
        print("Careful now! You're sending commands directly!")
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
    pcr_control = CaniPy(port="COM5", baud=baud_rate)

    if is_direct:
        pcr_control.direct_enable()

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
