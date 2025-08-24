import tkinter as Tkinter

try:
    import serial
except:
    print("Serial Library not available")

import time
import threading

from utils.canipy import CaniPy

baud_rate = 9600

logWin = None

def test_thread():
    time.sleep(1)
    iters = 10
    while iters != 0:
#        if (logWin != None):
#            logWin.insert(Tkinter.END,"Tick\n",("Activity"))
        print("Tick")
        time.sleep(2)
        iters -= 1

class xmapp_tk(Tkinter.Tk):  
    def __init__(self,parent):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()
        
        self.quitThread = False
        self.idleFrames = 0
        
        self.serialPort = None
        
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
        if self.serialPort != None:
            self.serialPort.close()
            self.serialPort = None

    def com_thread(self):
        # Keep calling the read method for the port
        while True:
            (return_code,data) = self.receiveXMPacket();
            if self.quitThread:
                return
            if return_code == None:
                continue
            code_val = return_code
            
            # check return codes

            match code_val:
                case 0x80:
                    self.print_status1(data)
                case 0x81:
                    self.logText.insert(Tkinter.END,"Goodnight\n",("Activity"))
                case 0x93:
                    self.print_mute_state(data)
                case 0xB1:
                    self.print_radio_id(data)
                case 0xC3:
                    self.print_signal_data(data)
                case 0xF2:
                    self.idleFrames += 1
                case 0xF4 | 0xFF:
                    if self.logText != None:
                        self.logText.insert(Tkinter.END,"Command Acknowledged\n",("Activity"))
                case _:
                    if self.logText != None:
                        self.logText.insert(Tkinter.END,f"Unknown return code {hex(code_val)}\n",("Warning"))
                

    def initialize(self):
        self.grid()
        
        self.ioText = None

        # Text window for debugging outpu
        
        self.logText = Tkinter.Text(self.parent,height=20,width=80,wrap=Tkinter.NONE)

        self.logText_vertScrollbar = Tkinter.Scrollbar(self.parent,orient=Tkinter.VERTICAL)
        self.logText_vertScrollbar.config(command=self.logText.yview)
        self.logText_horizScrollbar = Tkinter.Scrollbar(self.parent,orient=Tkinter.HORIZONTAL)
        self.logText_horizScrollbar.config(command=self.logText.xview)
        self.logText.configure(yscrollcommand=self.logText_vertScrollbar.set)
        self.logText.configure(xscrollcommand=self.logText_horizScrollbar.set)
        
        self.logText.grid(column=0,row=0,sticky='EWNS')
        
        self.logText_horizScrollbar.grid(column=0,row=1,sticky='EW')
        self.logText_vertScrollbar.grid(column=1,row=0,sticky='NS')

        self.logText.tag_config("Critical",foreground="red")
        self.logText.tag_config("Warning",foreground="orange")
        self.logText.tag_config("Activity",foreground="black")
        
        logWin = self.logText
        
        # text field for IO to/from radio
        self.ioText = Tkinter.Text(self.parent,height=10,width=80,wrap=Tkinter.NONE)
        self.ioText_vertScrollbar = Tkinter.Scrollbar(self.parent,orient=Tkinter.VERTICAL)
        self.ioText_vertScrollbar.config(command=self.ioText.yview)
        self.ioText_horizScrollbar = Tkinter.Scrollbar(self.parent,orient=Tkinter.HORIZONTAL)
        self.ioText_horizScrollbar.config(command=self.ioText.xview)
        self.ioText.configure(yscrollcommand=self.ioText_vertScrollbar.set)
        self.ioText.configure(xscrollcommand=self.ioText_horizScrollbar.set)
        
        self.ioText.grid(column=0,row=3,sticky='EWNS')
        
        self.ioText_horizScrollbar.grid(column=0,row=4,sticky='EW')
        self.ioText_vertScrollbar.grid(column=1,row=3,sticky='NS')
        
        self.ioText.tag_config("SentBytes",foreground="red")
        self.ioText.tag_config("ReceivedBytes",foreground="blue")
        
        # frame for command buttons
        self.buttonFrame = Tkinter.Frame(self.parent)
        
        # field for com port 
        self.comEntry = Tkinter.Entry(self.buttonFrame)
        self.comEntry.grid(column=0,row=0)
        self.comEntry.insert(Tkinter.END, "COM3")  #self.comEntry.set("COM3")
        
        self.powerOnButton = Tkinter.Button(self.buttonFrame,text="Power On",command=self.power_on)       
        self.powerOnButton.grid(column=3,row=0)
        
        self.powerOffButton = Tkinter.Button(self.buttonFrame,text="Power Off",command=self.power_off)       
        self.powerOffButton.grid(column=4,row=0)
        
        self.getRadioIDButton = Tkinter.Button(self.buttonFrame,text="Get Radio ID",command=self.get_radio_id)       
        self.getRadioIDButton.grid(column=5,row=0)
        
        self.GetSignalDataButton = Tkinter.Button(self.buttonFrame,text="Get Sig Data",command=self.get_signal_data)
        self.GetSignalDataButton.grid(column=6,row=0)

        muteoncmd = lambda: self.set_mute(True)
        self.MuteButton = Tkinter.Button(self.buttonFrame,text="Mute",command=muteoncmd)       
        self.MuteButton.grid(column=7,row=0)

        muteoffcmd = lambda: self.set_mute(False)
        self.UnmuteButton = Tkinter.Button(self.buttonFrame,text="Unmute",command=muteoffcmd)       
        self.UnmuteButton.grid(column=8,row=0)

        self.SetPcrDevice = Tkinter.Button(self.buttonFrame,text="PCR",command=self.set_pcr_device)
        self.SetPcrDevice.grid(column=1,row=0)

        self.SetPcrDevice = Tkinter.Button(self.buttonFrame,text="Direct",command=self.set_direct_device)
        self.SetPcrDevice.grid(column=2,row=0)

        self.SetWxDevice = Tkinter.Button(self.buttonFrame,text="WX Portable",command=self.set_wx_device)
        self.SetWxDevice.grid(column=1,row=1)

        self.SetWcDevice = Tkinter.Button(self.buttonFrame,text="WX Certified",command=self.set_wc_device)
        self.SetWcDevice.grid(column=2,row=1)

        self.buttonFrame.grid(column=0, row=5)
        
        self.resizable(True,False)
        self.update()
        self.geometry(self.geometry())
            
    def print_bin(self,buf,tag):
        bin_text = " ".join(f"{b:02X}" for b in buf) + "\n"
        self.ioText.insert(Tkinter.END,bin_text,tag)
    
    def sendXMPacket(self,cmd):
        # At some point move to just calling
        # the functions in util instead.
        # Using bytes() here would be better
        # as shown in the functions.
        packet = b""
        packet += cmd
        if self.serialPort != None:
            self.serialPort.pcr_tx(packet)
        if (self.ioText != None):
            self.print_bin(packet,("SentBytes")) 
        
    def receiveXMPacket(self):
        if self.serialPort == None:
            if self.logText != None:
                self.logText.insert(Tkinter.END,"No serial port to read\n",("Warning"))
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
                chunk = self.serialPort.serial_port.read(5-read_so_far)
            except:
                self.logText.insert(Tkinter.END,"No serial port to read\n",("Warning"))
                # wait for port to be connected
                time.sleep(1)
                return (None, None)
            packet += chunk
            read_so_far += len(chunk)
            #print "%d %d:" % (len(chunk),read_so_far)
            if (self.quitThread):
                return (None,None)
            
        if len(packet) != 5:
            if self.logText != None:
                self.logText.insert(Tkinter.END,f"Packet header size not as expected (5). {len(packet)}\n",("Warning"))
                return (None, None)
        # verify it is the header
        if packet[:2] != self.serialPort.header:
            if self.logText != None:
                self.logText.insert(Tkinter.END,f"Packet header not found: {packet[:2]}\n",("Warning"))
                return (None, None)
        size = packet[2]*256 + packet[3]
        # read the rest of the packet
        try:
            rest_of_packet = self.serialPort.serial_port.read(size+1)
        except:
            self.logText.insert(Tkinter.END,"No serial port to read\n",("Warning"))
            # wait for port to be connected
            time.sleep(1)
            return (None, None)
        if len(rest_of_packet) != size+1:
            if self.logText != None:
                self.logText.insert(Tkinter.END,f"Packet payload size not as expected({size}). {len(rest_of_packet)}\n",("Warning"))
                return (None, None)
        # return tuple with return code and data
        if self.ioText != None:
            self.print_bin(packet[4:]+rest_of_packet[:-2],"ReceivedBytes")  #ignore header, length, sum in printout
        return (packet[4],rest_of_packet[:size-1])
    
    def power_on(self):
        cmd = b'\x00\x16\x16\x24\x01'    
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Powering on radio\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def power_off(self):
        cmd = b'\x01\x01'    
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Powering off radio\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_radio_id(self):
        cmd = b'\x31'    
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting Radio ID\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def set_mute(self, on = False):
        cmd = b'\x13'
        
        if (on == True):
            logText = "Muting radio\n"
            cmd += b'\x01'
        else:
            logText = "Unmuting radio\n"
            cmd += b'\x00'
            
        if self.logText != None:
            self.logText.insert(Tkinter.END,logText,("Activity"))
            
        self.sendXMPacket(cmd)
    
    def change_channel(self,channel):
        cmd = b'\x10\x02' + channel + b'\x00\x00\x01'
        if self.logText != None:
            self.logText.insert(Tkinter.END,f"Changing Channel to {channel}\n",("Activity"))
        self.sendXMPacket(cmd)

    def change_data_channel(self,channel):
        cmd = b'\x10\x01' + channel + b'\x00\x00\x01'
        #cmd = b'\x10\x01' + channel + b'\x01\x00\x02'
        if self.logText != None:
            self.logText.insert(Tkinter.END,f"Changing Channel to {channel} in data mode\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_this_channel_info(self):
        cmd = b'\x25\x08'
        #cmd = b'\x25\x08' + channel + b'\x00'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting channel info\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_next_channel_info(self):
        cmd = b'\x25\x09'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting next channel info\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_previous_channel_info(self):
        cmd = b'\x25\x10'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting previous channel info\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_extended_channel_info(self,channel):
        cmd = b'\x22' + channel
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting extended channel info\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_signal_data(self):
        cmd = b'\x43'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting signal data\n",("Activity"))
        self.sendXMPacket(cmd)

    def ping_radio(self):
        cmd = b'\x4a\x43'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Pinging radio\n",("Activity"))
        self.sendXMPacket(cmd)

    def get_firmver(self):
        cmd = b'\x4a\x44'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting radio firmware version\n",("Activity"))
        self.sendXMPacket(cmd)

    def check_channel_status(self,channel):
        cmd = b'\x11' + channel + b'\x00'
        if self.logText != None:
            self.logText.insert(Tkinter.END,f"Checking status for Channel {channel}\n",("Activity"))
        self.sendXMPacket(cmd)

    def open_com_port(self):
        # Close com if any open
        if self.serialPort != None:
            self.serialPort.close()
            self.serialPort = None
        # get com port
        comPort = self.comEntry.get()
        if self.logText != None:
            self.logText.insert(Tkinter.END,f"Connect to {comPort} ({baud_rate})\n",("Activity"))
        # Begin to gently transplant CaniPy
        self.serialPort = CaniPy(port=comPort, baud=baud_rate)

    def set_pcr_device(self):
        global baud_rate
        baud_rate = 9600
        self.logText.insert(Tkinter.END,f"Baud rate set to PCR ({baud_rate})\n",("Activity"))
        self.open_com_port()
    
    def set_direct_device(self):
        self.set_pcr_device()
        self.logText.insert(Tkinter.END,f"Sending Direct enable commands\n",("Activity"))
        self.serialPort.direct_enable()

    def set_wx_device(self):
        global baud_rate
        baud_rate = 38400
        self.logText.insert(Tkinter.END,f"Baud rate set to WX Portable ({baud_rate})\n",("Activity"))
        self.open_com_port()

    def set_wc_device(self):
        global baud_rate
        baud_rate = 115200
        self.logText.insert(Tkinter.END,f"Baud rate set to WX Certified ({baud_rate})\n",("Activity"))
        self.open_com_port()

    def print_radio_id(self,data):
        if len(data) != 11:
            if self.logText != None:
                self.logText.insert(Tkinter.END,f"Radio id not correct length. Exp: 14 Act: {len(data)}\n",("Warning"))
            return
        # if good, print ascii characters
        if self.logText != None:
            self.logText.insert(Tkinter.END,f"Radio ID: {data[3:11].decode('ascii')}\n",("Activity"))
                                
    def print_status1(self,data):
        if len(data) != 26:
            if self.logText != None:
                self.logText.insert(Tkinter.END,f"Status1 not correct length. Exp: 11 Act: {len(data)}\n",("Warning"))
            #return
        # if good, print ascii characters
        status = "===Radio Info===\nActivated: "
        if data[0] == 0x3:
            status += "No"
        else:
            status += "Yes"
        status += f"\nVersion: {data[1]}.{data[2]}\n"
        status += f"RX Date: {data[2]}{data[3]}:{data[4]}{data[5]}:{data[6]}{data[7]}{data[8]}{data[9]}\n"
        status += f"CMB Version: {data[10]}\n"
        status += "%s"%data[12:20]
        if self.logText != None:
            self.logText.insert(Tkinter.END,f"{status}\n",("Activity"))
        
    def print_signal_data(self,data):
        if len(data) != 25:
            if self.logText != None:
                self.logText.insert(Tkinter.END,f"Signal data not correct length. Exp: 26 Act: {len(data)}\n",("Warning"))
            #return
        status = "===Receiver===\nSat: "
        if (data[2] == 0x0):
            status += "None"
        elif (data[2] == 0x1):
            status += "Fair"
        elif (data[2] == 0x2):
            status += "Good"
        elif (data[2] == 0x3):
            status += "Excellent"
        else:
            status += "?(%d)" % data[2]
            
        status += "\nAnt: "
        if (data[3] == 0x0):
            status += "Disconnected"
        elif (data[3] == 0x1):
            status += "Connected"
        else:
            status += "?(%d)" % data[3]
            
        if self.logText != None:
            self.logText.insert(Tkinter.END,f"{status}\n",("Activity"))

    def print_mute_state(self,data):
        status = "Mute: "
        if (data[2] == 0x00):
            status += "Off"
        elif (data[2] == 0x01):
            status += "On"            
        else:
            status += "?(%d)" % data[2]
            
        if self.logText != None:
            self.logText.insert(Tkinter.END,f"{status}\n",("Activity"))
        
if __name__ == "__main__":
    with xmapp_tk(None) as app:
        app.title('CaniPy')
        app.mainloop()
        
              
        
        
