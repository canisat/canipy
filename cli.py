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
    print("8. Toggle verbose output")
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
                pcr_control.change_channel(int(input("Channel #: ")))
                continue
            case "4":
                pcr_control.channel_info(int(input("Channel #: ")))
                continue
            case "5":
                pcr_control.get_radioid()
                continue
            case "6":
                pcr_control.signal_info()
                continue
            case "7":
                pcr_control.crash_override()
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
