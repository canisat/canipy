import serial
import time

class CaniPy:
    def __init__(self, port, baud:int=9600):
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

        self.set_port = lambda new_port: self.set_serial_params(new_port, self.baud_rate)  # "Are you smoking yet??"
        self.set_baud:Callable[[int], None] = lambda new_baud: self.set_serial_params(self.port_name, new_baud)

        self.serial_port = None
        self.set_serial_params(port, baud)

    def pcr_tx(self, payload:bytes):
        if self.serial_port == None:
            print("No serial port to read")
            return
        length = len(payload).to_bytes(2, byteorder='big')
        command = self.header + length + payload + self.tail
        self.serial_port.write(command)

    def power_up(self, ch_lbl:int=16, cat_lbl:int=16, title_lbl:int=24, loss_exp:bool=True):
        print("Powering up")
        self.pcr_tx(bytes([0x00, ch_lbl, cat_lbl, title_lbl, loss_exp]))

    def power_down(self, pwr_sav:bool=False):
        print("Powering down")
        self.pcr_tx(bytes([0x01, pwr_sav]))

    def change_channel(self, channel:int, data:bool=False):
        if channel not in range(256):
            print("Invalid channel value")
            return
        print(f"Changing to channel {channel}{' (Data)' if data else ''}")
        # Some data (i.e. channel 240/F0) is tuned with 01 00 02 instead of 00 00 01.
        # Not sure what those mean yet as other data tracks tune without this.
        self.pcr_tx(bytes([0x10, 0x01 if data else 0x02, channel, 0x00, 0x00, 0x01]))
        self.channel = channel

    def channel_info(self, channel:int):
        # Noting these cus they may still be valid.
        # These cmds are usually reserved for headunits
        # that look ahead/behind the current ch, and
        # when brute listing available channels
        #
        # self.pcr_tx(bytes([0x25, 0x08])) Curr ch
        # self.pcr_tx(bytes([0x25, 0x09])) Next ch
        # self.pcr_tx(bytes([0x25, 0x10])) Prev ch
        if channel not in range(256):
            print("Invalid channel value")
            return
        self.pcr_tx(bytes([0x25, 0x08, channel, 0x00]))
        print(f"Check pcap for info on channel {channel}")

    def channel_status(self, channel:int):
        if channel not in range(256):
            print("Invalid channel value")
            return
        # For checking sub status?
        self.pcr_tx(bytes([0x11, channel, 0x00]))
        print(f"Check pcap for status of channel {channel}")

    def audio_info(self, channel:int):
        # AKA "Extended" info; returns full artist+title info of playing content
        # I think just sending 22 would imply current channel
        if channel not in range(256):
            print("Invalid channel value")
            return
        self.pcr_tx(bytes([0x22, channel]))
        print(f"Check pcap for info on channel {channel}")

    def radio_id(self):
        self.pcr_tx(bytes([0x31]))
        print("Check pcap for ID")

    def signal_info(self):
        self.pcr_tx(bytes([0x43]))
        print("Check pcap for signal info")

    def set_mute(self, mute:bool):
        print(f"{'' if mute else 'Un-'}Muting Audio")
        self.pcr_tx(bytes([0x13, mute]))

    def ping_radio(self):
        # Response of CA 43 expected
        print("Ping")
        self.pcr_tx(bytes([0x4A, 0x43]))

    def get_firmver(self):
        self.pcr_tx(bytes([0x4A, 0x44]))
        print("Check pcap for firmware version")

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
    # def monitor_channel(self, channel, serv_mon:bool=False, prgtype_mon:bool=False, inf_mon:bool=False, ext_mon:bool=False):
    #     self.pcr_tx(bytes([0x50, channel, serv_mon, prgtype_mon, inf_mon, ext_mon]))
    #     print("Monitoring channel")
    
    def direct_enable(self):
        print("Direct listening mode")
        self.pcr_tx(bytes([0x74, 0x00, 0x01]))
        # These sleeps should be event driven instead
        time.sleep(1)

        print("Direct voltage on")
        self.pcr_tx(bytes([0x74, 0x02, 0x01, 0x01]))
        time.sleep(1)

        # No response would be received for this one
        # Just pretend it's all good after this
        print("Direct unmute DAC")
        self.pcr_tx(bytes([0x74, 0x0B, 0x00]))

    def set_serial_params(self, port, baud:int):
        try:
            self.serial_port = serial.Serial(port=port, baudrate=baud, timeout=1)
        except:
            print("No serial port to read")
            self.serial_port = None

    def close(self):
        if self.serial_port == None:
            print("No serial port to read")
            return
        self.serial_port.close()

    def crash_override(self):
        # FOR DEBUG USE
        print("Careful now! You're sending commands directly!")
        print("Hope you don't screw like you type!")
        self.pcr_tx(
            bytes.fromhex(
                input("Enter payload: ").strip().lower().replace("0x", "").replace(" ", "")
            )
        )
