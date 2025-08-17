import serial
import time

class PCRdevice:
    def __init__(self, port, baud):
        self.serial_port = serial.Serial(port=port, baudrate=baud, timeout=1)

        self.header = bytes([0x5A, 0xA5])
        self.tail = bytes([0xED, 0xED])

        self.mute = lambda: self.set_mute(True)
        self.unmute = lambda: self.set_mute(False)

    def pcr_tx(self, payload):
        length = len(payload).to_bytes(2, byteorder='big')
        command = self.header + length + payload + self.tail
        self.serial_port.write(command)

    def power_up(self, ch_lbl=16, cat_lbl=16, title_lbl=24, loss_exp:bool=True):
        print("Powering up")
        self.pcr_tx(bytes([0x00, ch_lbl, cat_lbl, title_lbl, loss_exp]))

    def power_down(self, pwr_sav:bool=False):
        print("Powering down")
        self.pcr_tx(bytes([0x01, pwr_sav]))

    def change_channel(self, channel, data:bool=False):
        # Some data (i.e. channel 240/F0) is tuned with 01 00 02 instead of 00 00 01.
        # Not sure what those mean yet as other data tracks tune without this.
        self.pcr_tx(bytes([0x10, 0x01 if data else 0x02, channel, 0x00, 0x00, 0x01]))
        print(f"Changed to channel {channel}{' (Data)' if data else ''}")

    def channel_info(self, channel):
        self.pcr_tx(bytes([0x25, 0x08, channel, 0x00]))
        # Noting these cus these may still be valid
        # Might implement something here later
        # maybe lambdas for curr/next/prev too?
        # self.pcr_tx(bytes([0x25, 0x08])) Curr ch
        # self.pcr_tx(bytes([0x25, 0x09])) Next ch
        # self.pcr_tx(bytes([0x25, 0x10])) Prev ch
        print(f"Check pcap for info on channel {channel}")

    def audio_info(self, channel):
        # AKA "Extended" info; returns full artist+title info of playing content
        # I think just sending 22 would imply current channel
        # Need to know what channel these things default to for tracking purposes..
        self.pcr_tx(bytes([0x22, channel]))
        print(f"Check pcap for info on channel {channel}")

    def radio_id(self):
        self.pcr_tx(bytes([0x31]))
        print("Check pcap for ID")

    def signal_info(self):
        self.pcr_tx(bytes([0x43]))
        print("Check pcap for signal info")

    def set_mute(self, mute:bool):
        self.pcr_tx(bytes([0x13, mute]))
        print(f"Audio {'' if mute else 'Un-'}Muted")

    def ping_radio(self):
        # Response of CA 43 expected
        self.pcr_tx(bytes([0x4A, 0x43]))
        print("Pinged radio")

    def get_firmver(self):
        self.pcr_tx(bytes([0x4A, 0x44]))
        print("Check pcap for firmware version")

    # Kept here for reference, but is event driven
    # So it's left unimplemented until handled
    # def monitor_channel(self, channel, serv_mon:bool=False, prgtype_mon:bool=False, inf_mon:bool=False, ext_mon:bool=False):
    #     self.pcr_tx(bytes([0x50, channel, serv_mon, prgtype_mon, inf_mon, ext_mon]))
    #     print("Monitoring channel")
    
    def direct_enable(self):
        print("Direct listening mode")
        self.pcr_tx(bytes([0x74, 0x00, 0x01]))
        time.sleep(5)

        print("Direct voltage on")
        self.pcr_tx(bytes([0x74, 0x02, 0x01, 0x01]))
        time.sleep(5)

        print("Direct unmute DAC")
        self.pcr_tx(bytes([0x74, 0x0B, 0x00]))
        time.sleep(5)

    def close(self):
        self.serial_port.close()

def get_option():
    choice = input().strip()
    if choice.isdigit():
        number = int(choice)
        if number >= 0 and number < 256:
            return number
    print("Invalid option.")
    return -1

def main():
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
        print("Select device:")

        choice = get_option()
        match choice:
            case 1:
                break
            case 2:
                is_direct = True
                break
            case 3:
                baud_rate = 38400
                break
            case 4:
                baud_rate = 115200
                break
            case 0:
                return

    # COM3 used for this test, change if necessary
    pcr_control = PCRdevice(port="COM3", baud=baud_rate)

    if is_direct:
        pcr_control.direct_enable()

    print("=XM Menu=")
    print("1. Power on")
    print("2. Power off")
    print("3. Tune channel")
    print("4. Fetch channel info")
    print("5. Fetch radio ID")
    print("6. Fetch signal info")
    print("0. Exit")

    # Pauses are used to pace the commands for this test
    time.sleep(5)

    while True:
        print("Select option:")

        choice = get_option()
        match choice:
            case 1:
                pcr_control.power_up()
            case 2:
                pcr_control.power_down()
            case 3:
                print("Channel #:")
                chnum = get_option()
                if chnum > 0 :
                    pcr_control.change_channel(chnum)
            case 4:
                print("Channel #:")
                chnum = get_option()
                if chnum > 0 :
                    pcr_control.channel_info(chnum)
            case 5:
                pcr_control.radio_id()
            case 6:
                pcr_control.signal_info()
            case 0:
                time.sleep(5)
                break

        time.sleep(5)

    pcr_control.close()

if __name__ == "__main__":
    main()
