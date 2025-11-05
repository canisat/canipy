import serial.tools.list_ports

from utils import CaniPy

def shell_main():
    """
    A very simple CaniPy setup.

    Used for debugging purposes
    and in environments without
    a graphical workspace.
    """

    # Default to PCR
    baud_rate = 9600
    is_direct = False

    device_list = {
        "1":("PCR",9600),
        "2":("Direct/Commander",9600),
        "3":("WX",38400),
        "4":("WX (Certified)",115200)
    }

    print("=Supported Devices=")
    for num, (name, _) in device_list.items():
        print(f"{num}. {name}")
    print("9. Simulator (Parse Payload)")
    print("0. Exit")

    while True:
        dev_select = input("Select device: ").strip()
        if dev_select == "0": return
        if dev_select in device_list:
            dev_name, baud_rate = device_list[dev_select]
            is_direct = (dev_name == "Direct/Commander")
            break
        if dev_select == "9":
            print("Careful now!")
            print("You're about to send manual commands to the conductor!")
            CaniPy().conductor.go(
                bytes.fromhex(
                    input(
                        "Enter payload: "
                    ).strip().lower().replace("0x","").replace(" ","")
                )
            )
            continue
        print("Invalid option")

    # List available COM ports
    ports_list = [port.device for port in serial.tools.list_ports.comports()]
    if ports_list:
        print("\n=Available Ports=")
        for num, port in enumerate(ports_list, start=1):
            print(f"{num}. {port}")
        print("0. Enter manually")

        while True:
            port_select = input("Select port: ").strip()
            if port_select == "0":
                port_path = input("Enter port path manually: ").strip()
                break
            if port_select.isdigit():
                if 1 <= int(port_select) <= len(ports_list):
                    port_path = ports_list[int(port_select) - 1]
                    break
            print("Invalid selection.")
    else:
        print("\nNo ports detected.")
        port_path = input("Enter port path manually: ").strip()

    if not port_path:
        print("No port provided. Exiting...")
        return

    pcr_control = CaniPy(port=port_path, baud=baud_rate)

    if is_direct:
        print("Using a Direct!")
        print("Device will power up by default")
        pcr_control.dx.enable()

    print("\n=Debug Menu=")
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
                pcr_control.tx.power_up()
                continue
            case "2":
                pcr_control.tx.power_down()
                continue
            case "3":
                pcr_control.tx.change_channel(int(input("Channel #: ")))
                continue
            case "4":
                pcr_control.tx.channel_info(int(input("Channel #: ")))
                continue
            case "5":
                pcr_control.tx.get_radioid()
                continue
            case "6":
                pcr_control.tx.signal_info()
                continue
            case "7":
                print("Careful now!")
                print("You're sending commands to the radio directly!")
                pcr_control.tx.send(
                    bytes.fromhex(
                        input("Enter payload: ").strip().lower().replace("0x", "").replace(" ", "")
                    )
                )
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
    shell_main()
