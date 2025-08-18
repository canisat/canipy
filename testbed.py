import time

from canipy import CaniPy

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
    pcr_control = CaniPy(port="COM3", baud=baud_rate)

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
