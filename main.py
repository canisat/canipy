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
        if self.canipy.serial_conn != None: self.canipy.close()

    def com_thread(self):
        # Keep calling the read method for the port
        while True:
            (return_code,data) = self.receiveXMPacket()
            if self.quitThread: return
            
            # check return codes
            # SOME ARE TEMPORARILY UNREFACTORED
            # AS THIS'LL LATER BE MOVED TO MODULE

            # data[0] and data[1] appear to always be
            # status code and detail respectively

            match return_code:
                case None:
                    continue
                case 0x80:
                    self.canipy.rx_startup(bytes([return_code])+data)
                case 0x81:
                    print("Goodnight")
                case 0x90:
                    if data[0] == 0x04:
                        print("No signal")
                        if data[1] == 0x10:
                            print("Check if antenna is connected")
                            print("and has a clear view of the sky")
                        continue
                    if self.canipy.verbose: print(f"Channel SID: {data[2]}")
                    if data[4]:
                        print(f"Data mode set on channel {data[3]}")
                    else:
                        self.canipy.channel_info(data[3])
                case 0x91:
                    # Need to be sure what 11/91 actually does...
                    if data[0] == 0x04:
                        print("No signal")
                    else:
                        print(f"Channel is {'' if data[0] == 0x01 else 'not '}present")
                        print("You will be tuned out!")
                        print("Change channel to resume content")
                case 0x93:
                    print(f"Mute: { {0x00:'Off',0x01:'On'}.get(data[2],f'?({data[2]})') }")
                case 0xA5:
                    self.canipy.rx_chan(bytes([return_code])+data)
                case 0xB1:
                    if len(data) != 11:
                        print("Invalid Radio ID length")
                        if self.canipy.verbose: print(f"Exp 11, got {len(data)}")
                        continue
                    # if good, print characters
                    print(f"Radio ID: {data[3:11].decode('utf-8')}")
                case 0xC1 | 0xC3:
                    self.canipy.rx_sig(bytes([return_code])+data)
                case 0xC2:
                    print("Signal strength monitoring status updated")
                case 0xCA:
                    # 'A' cmds are WX specific!
                    if data[0] == 0x43:
                        print("WX Pong")
                    elif data[0] == 0x64:
                        print(f"WX Version: {data[1:].decode('utf-8').rstrip(chr(0))}")
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
                    if data[0] == 0x01 and data[1] == 0x00:
                        # 01 00 (aka OK) on error, typically corresponds to antenna
                        print("Antenna not detected, check antenna")
                    if self.canipy.verbose:
                        print(f"{data[0]:02X} {data[1]:02X} {data[2:].decode('utf-8')}")
                    print("Radio may still be operated")
                    print("If errors persist, check radio")
                case _:
                    print(f"Unknown return code {hex(return_code)}")
                

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
        
    def receiveXMPacket(self):
        if self.canipy.serial_conn == None:
            # wait for port to be connected
            time.sleep(1)
            return (None, None)
            
        # read header 
        # first two bytes are 5AA5, like command
        # second two bytes are size.
        packet = b""
        read_so_far = 0
        while read_so_far < 5:
            chunk = b""
            try:
                chunk = self.canipy.serial_conn.read(5-read_so_far)
            except:
                print("No serial port in use")
                # wait for port to be connected
                time.sleep(1)
                return (None, None)
            packet += chunk
            read_so_far += len(chunk)
            #print(f"{len(chunk)} {read_so_far}:")
            if (self.quitThread): return (None,None)
            
        if len(packet) != 5:
            print("Unexpected header size")
            if self.canipy.verbose: print(f"Exp 5, got {len(packet)}")
            return (None, None)
        # verify it is the header
        if packet[:2] != self.canipy.header:
            print("Header not found")
            if self.canipy.verbose: print(f"{packet[:2]}")
            return (None, None)
        size = packet[2]*256 + packet[3]
        # read the rest of the packet
        try:
            rest_of_packet = self.canipy.serial_conn.read(size+1)
        except:
            print("No serial port in use")
            # wait for port to be connected
            time.sleep(1)
            return (None, None)
        if len(rest_of_packet) != size+1:
            print("Unexpected packet size")
            if self.canipy.verbose: print(f"Exp {size}, got {len(rest_of_packet)}")
            return (None, None)
        # return tuple with return code and data
        buf = packet[4:]+rest_of_packet[:-2]
        if self.canipy.verbose:
            print(f"Received: {" ".join(f"{b:02X}" for b in buf)}")  #ignore header, length, sum in printout
        return (packet[4],rest_of_packet[:size-1])
    
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
        if self.canipy.serial_conn != None: self.canipy.close()
        # get com port
        comPort = self.comEntry.get()
        print(f"Connect to {comPort} ({baud})")
        self.canipy.set_serial_params(port=comPort, baud=baud)

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
        
              
        
        
