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
        
        self.baud_rate = 9600
        
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
        if self.canipy.serial_conn != None:
            self.canipy.close()

    def com_thread(self):
        # Keep calling the read method for the port
        while True:
            (return_code,data) = self.receiveXMPacket()
            if self.quitThread:
                return
            
            # check return codes
            # TEMPORARILY UNREFACTORED FUNCTIONS
            # AS THEY'LL LATER BE MOVED TO MODULE

            match return_code:
                case None:
                    continue
                case 0x80:
                    if len(data) != 26:
                        print(f"Status1 not correct length. Exp: 11 Act: {len(data)}")
                        continue
                    # if good, print ascii characters
                    print("===Radio Info===")
                    print(f"Activated: {'No' if data[0] == 0x3 else 'Yes'}")
                    print(f"RX Version: {data[3]}")
                    print(f"RX Date: {data[4]:02X}/{data[5]:02X}/{data[6]:02X}{data[7]:02X}")
                    print(f"CMB Version: {data[12]}")
                    print(f"CMB Date: {data[13]:02X}/{data[14]:02X}/{data[15]:02X}{data[16]:02X}")
                    print(f"Radio ID: {data[18:26].decode('ascii')}")
                    print("================")
                case 0x81:
                    print("Goodnight")
                case 0x93:
                    print(f"Mute: { {0x00:'Off',0x01:'On'}.get(data[2],f'?({data[2]})') }")
                case 0xB1:
                    if len(data) != 11:
                        print(f"Radio id not correct length. Exp: 14 Act: {len(data)}")
                        continue
                    # if good, print ascii characters
                    print(f"Radio ID: {data[3:11].decode('ascii')}")
                case 0xCA:
                    # 4A/CA cmds are WX exclusive!
                    if data[0] == 0x43:
                        print("WX Pong")
                    elif data[0] == 0x64:
                        print(f"WX Version: {data[1:].decode('ascii').rstrip(chr(0))}")
                case 0xC3:
                    if len(data) != 25:
                        print(f"Signal data not correct length. Exp: 26 Act: {len(data)}")
                        continue
                    sigstrength = {0x00:"None",0x01:"Fair",0x02:"Good",0x03:"Excellent"}
                    antstrength = {0x00:"Disconnected",0x03:"Connected"}
                    print("===Receiver===")
                    print(f"Sat: {sigstrength.get(data[2],f'?({data[2]})')}")
                    print(f"Ant: {antstrength.get(data[3],f'?({data[3]})')}")
                    print(f"Ter: {sigstrength.get(data[4],f'?({data[4]})')}")
                    print("==============")
                case 0xE0:
                    print("PCR software can now start")
                case 0xF2:
                    self.idleFrames += 1
                case 0xF4:
                    print("Command Acknowledged")
                case 0xFF:
                    print(f"Commander Display: {data[2:].decode('ascii')}")
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

        self.SetDirectDevice = tkinter.Button(self.buttonFrame,text="Direct",command=self.set_direct_device)
        self.SetDirectDevice.grid(column=2,row=0)
        
        self.powerOnButton = tkinter.Button(self.buttonFrame,text="Power On",command=self.canipy.power_up)       
        self.powerOnButton.grid(column=3,row=0)
        
        self.powerOffButton = tkinter.Button(self.buttonFrame,text="Power Off",command=lambda:self.canipy.power_down(pwr_sav=True))       
        self.powerOffButton.grid(column=4,row=0)
        
        self.getRadioIDButton = tkinter.Button(self.buttonFrame,text="Get Radio ID",command=self.canipy.radio_id)       
        self.getRadioIDButton.grid(column=5,row=0)
        
        self.GetSignalDataButton = tkinter.Button(self.buttonFrame,text="Get Sig Data",command=self.canipy.signal_info)
        self.GetSignalDataButton.grid(column=6,row=0)

        self.MuteButton = tkinter.Button(self.buttonFrame,text="Mute",command=self.canipy.mute)       
        self.MuteButton.grid(column=7,row=0)

        self.UnmuteButton = tkinter.Button(self.buttonFrame,text="Unmute",command=self.canipy.unmute)       
        self.UnmuteButton.grid(column=8,row=0)

        # channel number 
        self.chEntry = tkinter.Entry(self.buttonFrame)
        self.chEntry.grid(column=0,row=1)
        self.chEntry.insert(tkinter.END, "1")

        self.SetWxDevice = tkinter.Button(self.buttonFrame,text="WX Portable",command=self.set_wx_device)
        self.SetWxDevice.grid(column=1,row=1)

        self.SetWcDevice = tkinter.Button(self.buttonFrame,text="WX Certified",command=self.set_wc_device)
        self.SetWcDevice.grid(column=2,row=1)

        self.changeChannelButton = tkinter.Button(self.buttonFrame,text="Change Ch",command=self.change_channel)       
        self.changeChannelButton.grid(column=3,row=1)

        self.getChInfoButton = tkinter.Button(self.buttonFrame,text="Ch Info",command=self.get_channel_info)       
        self.getChInfoButton.grid(column=4,row=1)

        self.extChInfoButton = tkinter.Button(self.buttonFrame,text="Ext Info",command=self.get_extended_channel_info)       
        self.extChInfoButton.grid(column=5,row=1)

        self.chStatusButton = tkinter.Button(self.buttonFrame,text="Ch Status",command=self.check_channel_status)       
        self.chStatusButton.grid(column=6,row=1)

        self.wxFwVerButton = tkinter.Button(self.buttonFrame,text="WX FirmVer",command=self.canipy.wx_firmver)       
        self.wxFwVerButton.grid(column=7,row=1)

        self.wxPingButton = tkinter.Button(self.buttonFrame,text="WX Ping",command=self.canipy.wx_ping)       
        self.wxPingButton.grid(column=8,row=1)

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
                print("No serial port to read")
                # wait for port to be connected
                time.sleep(1)
                return (None, None)
            packet += chunk
            read_so_far += len(chunk)
            #print "%d %d:" % (len(chunk),read_so_far)
            if (self.quitThread):
                return (None,None)
            
        if len(packet) != 5:
            print(f"Packet header size not as expected (5). {len(packet)}")
            return (None, None)
        # verify it is the header
        if packet[:2] != self.canipy.header:
            print(f"Packet header not found: {packet[:2]}")
            return (None, None)
        size = packet[2]*256 + packet[3]
        # read the rest of the packet
        try:
            rest_of_packet = self.canipy.serial_conn.read(size+1)
        except:
            print("No serial port to read")
            # wait for port to be connected
            time.sleep(1)
            return (None, None)
        if len(rest_of_packet) != size+1:
            print(f"Packet payload size not as expected({size}). {len(rest_of_packet)}")
            return (None, None)
        # return tuple with return code and data
        buf = packet[4:]+rest_of_packet[:-2]
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
        
    def get_this_channel_info(self):
        print("Getting current channel info")
        self.canipy.pcr_tx(bytes([0x25, 0x08]))
        
    def get_next_channel_info(self):
        print("Getting next channel info")
        self.canipy.pcr_tx(bytes([0x25, 0x09]))
        
    def get_previous_channel_info(self):
        print("Getting previous channel info")
        self.canipy.pcr_tx(bytes([0x25, 0x10]))
        
    def get_extended_channel_info(self):
        channel = int(self.chEntry.get())
        self.canipy.audio_info(channel)

    def check_channel_status(self):
        channel = int(self.chEntry.get())
        self.canipy.channel_status(channel)

    def open_com_port(self):
        # Close com if any open
        if self.canipy.serial_conn != None:
            self.canipy.close()
        # get com port
        comPort = self.comEntry.get()
        print(f"Connect to {comPort} ({self.baud_rate})")
        self.canipy.set_serial_params(port=comPort, baud=self.baud_rate)

    def set_pcr_device(self):
        self.baud_rate = 9600
        print(f"Baud rate set to PCR ({self.baud_rate})")
        self.open_com_port()
    
    def set_direct_device(self):
        self.set_pcr_device()
        print(f"Sending Direct enable commands")
        self.canipy.direct_enable()

    def set_wx_device(self):
        self.baud_rate = 38400
        print(f"Baud rate set to WX Portable ({self.baud_rate})")
        self.open_com_port()

    def set_wc_device(self):
        self.baud_rate = 115200
        print(f"Baud rate set to WX Certified ({self.baud_rate})")
        self.open_com_port()
        
if __name__ == "__main__":
    with canipy_tk(None) as app:
        app.title('CaniPy')
        app.mainloop()
        
              
        
        
