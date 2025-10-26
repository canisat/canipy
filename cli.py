from utils import CaniPy

def shell_main():
    """
    A very simple CaniPy setup.

    Used for debugging purposes
    and in environments without
    a graphical environment.
    """

    # Default to PCR
    baud_rate = 9600
    is_direct = False

    print("=Supported Devices=")
    print("1. PCR")
    print("2. Direct/Commander")
    print("3. WX")
    print("4. WX (Certified)")
    print("5. Simulator (Parse Payload)")
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
            case "5":
                print("Careful now!")
                print("You're about to send manual commands to the conductor!")
                CaniPy().conductor.go(
                    bytes.fromhex(
                        input("Enter payload: ").strip().lower().replace("0x", "").replace(" ", "")
                    )
                )
                continue
            case "0":
                return
        print("Invalid option")

    # COM3 used for this test, change if necessary
    pcr_control = CaniPy(port="COM3", baud=baud_rate)

    if is_direct: pcr_control.dx.enable()

    print("=Debug Menu=")
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
