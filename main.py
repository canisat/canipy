import tkinter

import time
import threading

from utils.canipy import CaniPy

class canipy_tk(tkinter.Tk):  
    def __init__(self,parent):
        self.canipy = CaniPy()

        tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()
        
        self.quitThread = False
        self.idleFrames = 0
        
        # start com port read thread
        self.comThread = threading.Thread(None,self.com_thread,"ComThread")
        self.comThread.start()
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Stop thread upon window exit
        self.quitThread = True
        self.comThread.join(None)
        # Close com if any open
        if self.canipy.serial_conn is not None: self.canipy.close()

    def com_thread(self):
        # Keep calling the read method for the port
        while True:
            rx_response = self.rx_packet()
            if self.quitThread: return
            if not rx_response: continue
            
            # check return codes
            # THIS SWITCH IS TO BE REFACTORED!!

            # rx_response[1] and rx_response[2] appear to
            # always be status code and detail respectively

            match rx_response[0]:
                case 0x80:
                    self.canipy.rx_startup(rx_response)
                case 0x81:
                    print("Goodnight")
                case 0x90:
                    if rx_response[1] == 0x04:
                        print("No signal")
                        if rx_response[2] == 0x10:
                            print("Check if antenna is connected")
                            print("and has a clear view of the sky")
                        continue
                    if self.canipy.verbose: print(f"Channel SID: {rx_response[3]}")
                    if rx_response[5]:
                        print(f"Data mode set on channel {rx_response[4]}")
                    else:
                        self.canipy.channel_info(rx_response[4])
                case 0x91:
                    # Need to be sure what 11/91 actually does...
                    if rx_response[1] == 0x04:
                        print("No signal")
                    else:
                        print(f"Channel is {'' if rx_response[1] == 0x01 else 'not '}present")
                        print("You will be tuned out!")
                        print("Change channel to resume content")
                case 0x93:
                    print(f"Mute: { {0x00:'Off',0x01:'On'}.get(rx_response[3],f'?({rx_response[3]})') }")
                case 0xA5:
                    self.canipy.rx_chan(rx_response)
                case 0xB1:
                    if len(rx_response) != 12:
                        print("Invalid Radio ID length")
                        if self.canipy.verbose: print(f"Exp 12, got {len(rx_response)}")
                        continue
                    # if good, print characters
                    print(f"Radio ID: {rx_response[4:12].decode('utf-8')}")
                case 0xC1 | 0xC3:
                    self.canipy.rx_sig(rx_response)
                case 0xC2:
                    print("Signal strength monitoring status updated")
                case 0xCA:
                    # 'A' cmds are WX specific!
                    if rx_response[1] == 0x43:
                        print("WX Pong")
                    elif rx_response[1] == 0x64:
                        print(f"WX Version: {rx_response[2:].decode('utf-8').rstrip(chr(0))}")
                case 0xE0:
                    print("Fetched activation info")
                case 0xE1:
                    print("Fetched deactivation info")
                case 0xF2:
                    # Direct idle frames.
                    # Counted, but generally just ignored.
                    self.idleFrames += 1
                case 0xF4:
                    # Acknowledgement of Direct responses.
                    # nsayer ref mistakenly listens to E4??
                    print("Command Acknowledged")
                case 0xFF:
                    # These usually can be recovered from
                    print("Warning! Radio reported an error")
                    if rx_response[1] == 0x01 and rx_response[2] == 0x00:
                        # 01 00 (aka OK) on error, typically corresponds to antenna
                        print("Antenna not detected, check antenna")
                    if rx_response[1] == 0x07 and rx_response[2] == 0x10:
                        # 07 10, sending commands to a radio tuner that is not on yet
                        print("Please power up the tuner before sending commands")
                    if self.canipy.verbose:
                        print(f"{rx_response[1]:02X} {rx_response[2]:02X} {rx_response[3:].decode('utf-8')}")
                    print("Radio may still be operated")
                    print("If errors persist, check radio")
                case _:
                    print(f"Unknown return code {hex(rx_response[0])}")
                

    def initialize(self):
        self.grid()
        
        # frame for command buttons
        self.buttonFrame = tkinter.Frame(self.parent)
        
        # field for com port 
        self.comEntry = tkinter.Entry(self.buttonFrame)
        self.comEntry.grid(column=0,row=0)
        self.comEntry.insert(tkinter.END, "COM3")  #self.comEntry.set("COM3")
        
        self.SetPcrDevice = tkinter.Button(self.buttonFrame,text="PCR",command=self.set_pcr_device)
        self.SetPcrDevice.grid(column=1,row=0)

        self.SetWxDevice = tkinter.Button(self.buttonFrame,text="WX Portable",command=self.set_wx_device)
        self.SetWxDevice.grid(column=2,row=0)
        
        self.powerOnButton = tkinter.Button(self.buttonFrame,text="Power On",command=self.canipy.power_up)       
        self.powerOnButton.grid(column=3,row=0)
        
        self.changeChannelButton = tkinter.Button(self.buttonFrame,text="Change Ch",command=self.change_channel)       
        self.changeChannelButton.grid(column=4,row=0)
        
        self.getRadioIDButton = tkinter.Button(self.buttonFrame,text="Get Radio ID",command=self.canipy.radio_id)       
        self.getRadioIDButton.grid(column=5,row=0)
        
        self.GetSignalDataButton = tkinter.Button(self.buttonFrame,text="Get Sig Data",command=self.canipy.signal_info)
        self.GetSignalDataButton.grid(column=6,row=0)

        self.MuteButton = tkinter.Button(self.buttonFrame,text="Mute",command=self.canipy.mute)       
        self.MuteButton.grid(column=7,row=0)

        # channel number 
        self.chEntry = tkinter.Entry(self.buttonFrame)
        self.chEntry.grid(column=0,row=1)
        self.chEntry.insert(tkinter.END, "1")

        self.SetDirectDevice = tkinter.Button(self.buttonFrame,text="Direct",command=self.set_direct_device)
        self.SetDirectDevice.grid(column=1,row=1)

        self.SetWcDevice = tkinter.Button(self.buttonFrame,text="WX Certified",command=self.set_wc_device)
        self.SetWcDevice.grid(column=2,row=1)

        self.powerOffButton = tkinter.Button(self.buttonFrame,text="Power Off",command=lambda:self.canipy.power_down(pwr_sav=True))       
        self.powerOffButton.grid(column=3,row=1)

        self.getChInfoButton = tkinter.Button(self.buttonFrame,text="Ch Info",command=self.get_channel_info)       
        self.getChInfoButton.grid(column=4,row=1)

        self.extChInfoButton = tkinter.Button(self.buttonFrame,text="Ext Ch Info",command=self.get_extended_channel_info)       
        self.extChInfoButton.grid(column=5,row=1)

        self.chStatusButton = tkinter.Button(self.buttonFrame,text="Watch Sig",command=self.canipy.sigmon_enable)       
        self.chStatusButton.grid(column=6,row=1)

        self.UnmuteButton = tkinter.Button(self.buttonFrame,text="Unmute",command=self.canipy.unmute)       
        self.UnmuteButton.grid(column=7,row=1)
        
        # Might repurpose these buttons for someting else down the road...
        #
        # self.wxFwVerButton = tkinter.Button(self.buttonFrame,text="WX FirmVer",command=self.canipy.wx_firmver)       
        # self.wxFwVerButton.grid(column=7,row=1)
        # self.wxPingButton = tkinter.Button(self.buttonFrame,text="WX Ping",command=self.canipy.wx_ping)       
        # self.wxPingButton.grid(column=8,row=1)

        self.buttonFrame.grid(column=0, row=0)
        
        self.resizable(False,False)
        self.update()
        self.geometry(self.geometry())
        
    def rx_packet(self) -> bytes:
        if self.canipy.serial_conn is None:
            # wait for port to be connected
            time.sleep(1)
            return b""
            
        # read header 
        # first two bytes are 5AA5, like command
        # second two bytes are size.
        packet = b""
        read_so_far = 0
        while read_so_far < 5:
            try:
                chunk = self.canipy.serial_conn.read(5-read_so_far)
            except:
                print("No serial port in use")
                # wait for port to be connected
                time.sleep(1)
                return b""
            packet += chunk
            read_so_far += len(chunk)
            #print(f"{len(chunk)} {read_so_far}:")
            if self.quitThread: return b""
            
        if len(packet) != 5:
            print("Unexpected header size")
            if self.canipy.verbose: print(f"Exp 5, got {len(packet)}")
            return b""
        # verify it is the header
        if packet[:2] != self.canipy.header:
            print("Header not found")
            if self.canipy.verbose: print(f"{packet[:2]}")
            return b""
        size = packet[2]*256 + packet[3]
        # read the rest of the packet
        try:
            rest_of_packet = self.canipy.serial_conn.read(size+1)
        except:
            print("No serial port in use")
            # wait for port to be connected
            time.sleep(1)
            return b""
        if len(rest_of_packet) != size+1:
            print("Unexpected packet size")
            if self.canipy.verbose: print(f"Exp {size}, got {len(rest_of_packet)}")
            return b""
        # combine the return code and data and return
        # ignoring header, length, sum in printout
        buf = packet[4:]+rest_of_packet[:-2]
        if self.canipy.verbose:
            print(f"Received: {' '.join(f'{b:02X}' for b in buf)}")
        #return bytes([packet[4]])+rest_of_packet[:size-1]
        return buf
    
    def change_channel(self):
        channel = int(self.chEntry.get())
        self.canipy.change_channel(channel)

    def change_data_channel(self):
        channel = int(self.chEntry.get())
        self.canipy.change_channel(channel, data=True)

    def get_channel_info(self):
        channel = int(self.chEntry.get())
        self.canipy.channel_info(channel)
        
    def get_extended_channel_info(self):
        channel = int(self.chEntry.get())
        self.canipy.audio_info(channel)

    def open_com_port(self, baud:int=9600):
        # Close com if any open
        if self.canipy.serial_conn is not None: self.canipy.close()
        # get com port
        com_port = self.comEntry.get()
        print(f"Connect to {com_port} ({baud})")
        self.canipy.set_serial_params(port=com_port, baud=baud)

    def set_pcr_device(self):
        print("Device set to PCR")
        self.open_com_port()
    
    def set_direct_device(self):
        self.set_pcr_device()
        print("Sending Direct enable commands")
        self.canipy.direct_enable()

    def set_wx_device(self):
        print("Device set to WX (Portable)")
        self.open_com_port(baud=38400)

    def set_wc_device(self):
        print("Device set to WX (Certified)")
        self.open_com_port(baud=115200)
        
if __name__ == "__main__":
    with canipy_tk(None) as app:
        app.title('CaniPy')
        app.mainloop()
        
              
        
        
