import tkinter

import time
import threading

from utils import CaniPy

class canipy_tk(tkinter.Tk):  
    def __init__(self,parent):
        self.canipy = CaniPy()

        tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()
        
        self.quitThread = False
        
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
            buf = self.rx_packet()
            if self.quitThread: return
            if not buf: continue  # sure wish i was buff..
            self.canipy.rx_response(buf)
                
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
        
        self.getRadioIDButton = tkinter.Button(self.buttonFrame,text="Get Radio ID",command=self.canipy.get_radioid)       
        self.getRadioIDButton.grid(column=5,row=0)
        
        self.GetSignalDataButton = tkinter.Button(self.buttonFrame,text="Get Sig Data",command=self.canipy.signal_info)
        self.GetSignalDataButton.grid(column=6,row=0)

        self.MuteButton = tkinter.Button(self.buttonFrame,text="Mute",command=self.canipy.mute)       
        self.MuteButton.grid(column=7,row=0)

        self.clockOnButton = tkinter.Button(self.buttonFrame,text="Clock On",command=lambda:self.canipy.clock_mon(True))       
        self.clockOnButton.grid(column=8,row=0)

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

        self.sigMonButton = tkinter.Button(self.buttonFrame,text="Watch Sig",command=self.canipy.sigmon_enable)       
        self.sigMonButton.grid(column=6,row=1)

        self.UnmuteButton = tkinter.Button(self.buttonFrame,text="Unmute",command=self.canipy.unmute)       
        self.UnmuteButton.grid(column=7,row=1)
        
        self.clockOffButton = tkinter.Button(self.buttonFrame,text="Clock Off",command=lambda:self.canipy.clock_mon(False))       
        self.clockOffButton.grid(column=8,row=1)
        
        # Buttons used during debug
        #
        # self.wxFwVerButton = tkinter.Button(self.buttonFrame,text="WX FirmVer",command=self.canipy.wx_firmver)       
        # self.wxFwVerButton.grid(column=9,row=0)
        # self.wxPingButton = tkinter.Button(self.buttonFrame,text="WX Ping",command=self.canipy.wx_ping)       
        # self.wxPingButton.grid(column=9,row=1)

        self.buttonFrame.grid(column=0, row=0)
        
        self.resizable(False,False)
        self.update()
        self.geometry(self.geometry())
        
    def rx_packet(self) -> bytes:
        if self.canipy.serial_conn is None or not self.canipy.serial_conn.is_open:
            # wait for port to be connected
            time.sleep(1)
            return b""
            
        # read header 
        # first two bytes are 5AA5, like command
        # second two bytes are size.
        packet = b""
        read_so_far = 0
        while read_so_far < 5:
            # Because this is a threaded function, serial_conn can
            # change to None at ANY MOMENT, even if it clears the
            # check at the start of this function!
            # Best to handle exceptions to cater those edge cases.
            #if self.canipy.serial_conn is None or not self.canipy.serial_conn.is_open:
            try:
                chunk = self.canipy.serial_conn.read(5-read_so_far)
            except Exception as e:
                if self.canipy.verbose: (type(e))
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
            if self.canipy.verbose: print(packet[:2])
            return b""
        # Both of these do the same thing, but codebase
        # is to keep consistency with the more
        # biblically accurate bitwise operation...
        #size = packet[2]*256 + packet[3]
        size = (packet[2] << 8) | packet[3]
        # read the rest of the packet
        #if self.canipy.serial_conn is None or not self.canipy.serial_conn.is_open:
        try:
            rest_of_packet = self.canipy.serial_conn.read(size+1)
        except Exception as e:
            if self.canipy.verbose: (type(e))
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
        self.canipy.ext_info(channel)

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
        
              
        
        
