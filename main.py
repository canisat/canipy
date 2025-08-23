import tkinter as Tkinter

try:
    import serial
except:
    print("Serial Library not available")

import time
import threading

from utils.canipy import CaniPy

xm_cmd_header = b"\x5A\xA5"
xm_cmd_footer = b"\xED\xED" 

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
        
        # start com port read thread
        
        self.comThread = threading.Thread(None,self.com_thread,"ComThread")
        self.comThread.start()
        
    def com_thread(self):
        # Keep calling the read method for the port
        if self.logText != None:
            self.logText.insert(Tkinter.END,"COM port thread started\n",("Activity"))
        while True:
            (return_code,data) = self.receiveXMPacket();
            if self.quitThread:
                return
            if return_code == None:
                continue
            code_val = return_code
            
            # check return codes

            if code_val == 0xF2:
                self.idleFrames += 1
            elif code_val == 0xF4:
                if self.logText != None:
                    self.logText.insert(Tkinter.END,"Command Acknowledged\n",("Activity"))
            if code_val == 0xB1:
                self.print_radio_id(data)
            elif code_val == 0x80:
                self.print_status1(data)
            elif code_val == 0xC3:
                self.print_signal_data(data)
            elif code_val == 0x93:
                self.print_mute_state(data)
            else:
                if self.logText != None:
                    self.logText.insert(Tkinter.END,"Unknown return code 0x%02X\n"%code_val,("Warning"))
                

    def initialize(self):
        self.grid()
        
        self.ioText = None
        self.serialPort = None

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
        
        # button for opening port
        self.OpenButton = Tkinter.Button(self.buttonFrame,text="Open",command=self.open_com_port)       
        self.OpenButton.grid(column=1,row=0)
        
        # button for closing port
        self.CloseButton = Tkinter.Button(self.buttonFrame,text="Close",command=self.close_com_port)       
        self.CloseButton.grid(column=2,row=0)
        
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

        self.SetPcrDevice = Tkinter.Button(self.buttonFrame,text="PCR/Direct",command=self.set_pcr_device)
        self.SetPcrDevice.grid(column=0,row=1)

        self.SetWxDevice = Tkinter.Button(self.buttonFrame,text="WX Portable",command=self.set_wx_device)
        self.SetWxDevice.grid(column=1,row=1)

        self.SetWcDevice = Tkinter.Button(self.buttonFrame,text="WX Certified",command=self.set_wc_device)
        self.SetWcDevice.grid(column=2,row=1)

        # button for killing com thread
        self.KillThreadButton = Tkinter.Button(self.buttonFrame,text="Kill COM thread",command=self.kill_thread)       
        self.KillThreadButton.grid(column=3,row=1)

        self.resetXmButton = Tkinter.Button(self.buttonFrame,text="Direct Cmd",command=self.reset_xm)       
        self.resetXmButton.grid(column=4,row=1)

        self.turnOn33VButton = Tkinter.Button(self.buttonFrame,text="Direct 3.3V",command=self.turn_on_33V)       
        self.turnOn33VButton.grid(column=5,row=1)
        
        self.unmuteDacButton = Tkinter.Button(self.buttonFrame,text="Direct DAC",command=self.unmute_dac)       
        self.unmuteDacButton.grid(column=6,row=1)

        self.buttonFrame.grid(column=0, row=5)
        
        self.resizable(True,False)
        self.update()
        self.geometry(self.geometry())
    
    def kill_thread(self):
        self.quitThread = True
        self.comThread.join(None)
        self.logText.insert(Tkinter.END,"COM thread killed.\n",("Activity"))    
            
    def print_bin(self,buf,tag):
        bin_text = " ".join(f"{b:02X}" for b in buf) + "\n"
        self.ioText.insert(Tkinter.END,bin_text,tag)
    
    def sendXMPacket(self,cmd):
        packet = b""
        packet += xm_cmd_header + b'\x00'
        packet += cmd
        packet += xm_cmd_footer
        if self.serialPort != None:
            # TODO: move to pcr_tx() instead
            # However, this script has the byte lengths baked
            # rather than calculating them on demand.
            # That will gradually be installed here later.
            # For now, write directly to the port.
            self.serialPort.serial_port.write(packet)
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
                self.logText.insert(Tkinter.END,"Packet header size not as expected (5). %d\n"%len(packet),("Warning"))
                return (None, None)
        # verify it is the header
        if packet[:2] != xm_cmd_header:
            if self.logText != None:
                self.logText.insert(Tkinter.END,"Packet header not found: %s\n"%packet[:2],("Warning"))
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
                self.logText.insert(Tkinter.END,"Packet payload size not as expected(%d). %d\n"%(size,len(rest_of_packet)),("Warning"))
                return (None, None)
        # return tuple with return code and data
        if self.ioText != None:
            self.print_bin(packet+rest_of_packet,"ReceivedBytes")
        return (packet[4],rest_of_packet[:size-1])
     
    def set_pcr_device(self):
        global baud_rate
        baud_rate = 9600
        self.logText.insert(Tkinter.END,f"Baud rate set to PCR ({baud_rate})\n",("Activity"))

    def set_wx_device(self):
        global baud_rate
        baud_rate = 38400
        self.logText.insert(Tkinter.END,f"Baud rate set to WX Portable ({baud_rate})\n",("Activity"))

    def set_wc_device(self):
        global baud_rate
        baud_rate = 115200
        self.logText.insert(Tkinter.END,f"Baud rate set to WX Certified ({baud_rate})\n",("Activity"))
    
    def reset_xm(self):
        cmd = b'\x03\x74\x00\x01'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Resetting radio\n",("Activity"))
        self.sendXMPacket(cmd)
    
    def turn_on_33V(self):
        cmd = b'\x04\x74\x02\x01\x01'    
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Turning on 3.3\n",("Activity"))
        self.sendXMPacket(cmd)
    
    def unmute_dac(self):
        cmd = b'\x03\x74\x0B\x00'    
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Unmuting DAC\n",("Activity"))
        self.sendXMPacket(cmd)
    
    def power_on(self):
        cmd = b'\x05\x00\x16\x16\x24\x01'    
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Powering on radio\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def power_off(self):
        cmd = b'\x02\x01\x01'    
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Powering off radio\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_radio_id(self):
        cmd = b'\x01\x31'    
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting Radio ID\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def set_mute(self, on = False):
        cmd = b'\x02\x13'
        
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
        cmd = b'\x06\x10\x02' + channel + b'\x00\x00\x01'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Changing Channel to %d\n"%channel,("Activity"))
        self.sendXMPacket(cmd)

    def change_data_channel(self,channel):
        cmd = b'\x06\x10\x01' + channel + b'\x00\x00\x01'
        #cmd = b'\x06\x10\x01' + channel + b'\x01\x00\x02'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Changing Channel to %d in data mode\n"%channel,("Activity"))
        self.sendXMPacket(cmd)
        
    def get_this_channel_info(self):
        cmd = b'\x02\x25\x08'
        #cmd = b'\x04\x25\x08' + channel + b'\x00'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting channel info\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_next_channel_info(self):
        cmd = b'\x02\x25\x09'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting next channel info\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_previous_channel_info(self):
        cmd = b'\x02\x25\x10'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting previous channel info\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_extended_channel_info(self,channel):
        cmd = b'\x02\x22' + channel
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting extended channel info\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_signal_data(self):
        cmd = b'\x01\x43'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting signal data\n",("Activity"))
        self.sendXMPacket(cmd)

    def ping_radio(self):
        cmd = b'\x02\x4a\x43'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Pinging radio\n",("Activity"))
        self.sendXMPacket(cmd)

    def get_firmver(self):
        cmd = b'\x02\x4a\x44'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting radio firmware version\n",("Activity"))
        self.sendXMPacket(cmd)

    def check_channel_status(self,channel):
        cmd = b'\x03\x11' + channel + b'\x00'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Checking status for Channel %d\n"%channel,("Activity"))
        self.sendXMPacket(cmd)

    def open_com_port(self):
        # get com port
        comPort = self.comEntry.get()
        # Begin to gently transplant CaniPy
        self.serialPort = CaniPy(port=comPort, baud=baud_rate)

    def close_com_port(self):
        if self.serialPort != None:
            self.serialPort.close()
            self.serialPort = None

    def print_radio_id(self,data):
        if len(data) != 11:
            if self.logText != None:
                self.logText.insert(Tkinter.END,"Radio id not correct length. Exp: 14 Act: %d\n"%len(data),("Warning"))
            return
        # if good, print ascii characters
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Radio ID: " + data[3:11].decode('ascii') + "\n",("Activity"))
                                
    def print_status1(self,data):
        if len(data) != 26:
            if self.logText != None:
                self.logText.insert(Tkinter.END,"Status1 not correct length. Exp: 11 Act: %d\n"%len(data),("Warning"))
            #return
        # if good, print ascii characters
        status = "Radio Info"
        if data[0] == 0x3:
            status += " (Not Activated)"
        status += ":\nVersion: %d.%d\n"%(data[1],data[2])
        status += "RX Date: %d%d:%d%d:%d%d%d%d\n"%(data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9])
        status += "CMB Version: %d\n"%data[10]
        status += "%s"%data[12:20]
        if self.logText != None:
            self.logText.insert(Tkinter.END,status + "\n",("Activity"))
        
    def print_signal_data(self,data):
        if len(data) != 25:
            if self.logText != None:
                self.logText.insert(Tkinter.END,"Signal data not correct length. Exp: 26 Act: %d\n"%len(data),("Warning"))
            #return
        status = "Receiver:\nSat: "
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
            self.logText.insert(Tkinter.END,status + "\n",("Activity"))

    def print_mute_state(self,data):
        status = "Mute: "
        if (data[2] == 0x00):
            status += "Off"
        elif (data[2] == 0x01):
            status += "On"            
        else:
            status += "?(%d)" % data[2]
            
        if self.logText != None:
            self.logText.insert(Tkinter.END,status + "\n",("Activity"))
        
if __name__ == "__main__":
    app = xmapp_tk(None)
    app.title('CaniPy')
    app.mainloop()
        
              
        
        
