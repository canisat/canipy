import serial
import time

class PCRdevice:
    def __init__(self, port, baud):
        self.serial_port = serial.Serial(port=port, baudrate=baud, timeout=1)
        self.header = bytes([0x5A, 0xA5])
        self.tail = bytes([0xED, 0xED])

    def pcr_tx(self, payload):
        length = len(payload).to_bytes(2, byteorder='big')
        command = self.header + length + payload + self.tail
        self.serial_port.write(command)

    def power_up(self):
        payload = bytes([0x00, 0x10, 0x10, 0x10, 0x01])
        print("Powering up")
        self.pcr_tx(payload)

    def power_down(self):
        payload = bytes([0x01, 0x00])
        print("Powering down")
        self.pcr_tx(payload)

    def change_channel(self, channel):
        payload = bytes([0x10, 0x02, channel, 0x00, 0x00, 0x01])
        self.pcr_tx(payload)
        print(f"Changed to channel {channel}")

    def channel_info(self, channel):
        payload = bytes([0x25, 0x08, channel, 0x00])
        self.pcr_tx(payload)
        print(f"Check pcap for info on channel {channel}")

    def radio_id(self):
        payload = bytes([0x31])
        self.pcr_tx(payload)
        print("Check pcap for ID")

    def signal_info(self):
        payload = bytes([0x43])
        self.pcr_tx(payload)
        print("Check pcap for signal info")
    
    def direct_enable(self):
        payload = bytes([0x74, 0x00, 0x01])
        print("Direct listening mode")
        self.pcr_tx(payload)

        time.sleep(5)

        payload = bytes([0x74, 0x02, 0x01, 0x01])
        print("Direct voltage on")
        self.pcr_tx(payload)

        time.sleep(5)

        payload = bytes([0x74, 0x0B, 0x00])
        print("Direct unmute DAC")
        self.pcr_tx(payload)

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
