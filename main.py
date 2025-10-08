import tkinter

from utils import CaniPy

class canipy_tk(tkinter.Tk):  
    def __init__(self,parent):
        self.canipy = CaniPy()

        tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

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
        
        self.powerOnButton = tkinter.Button(self.buttonFrame,text="Power On",command=self.canipy.tx.power_up)       
        self.powerOnButton.grid(column=3,row=0)
        
        self.changeChannelButton = tkinter.Button(self.buttonFrame,text="Change Ch",command=self.change_channel)       
        self.changeChannelButton.grid(column=4,row=0)
        
        self.getRadioIDButton = tkinter.Button(self.buttonFrame,text="Get Radio ID",command=self.canipy.tx.get_radioid)       
        self.getRadioIDButton.grid(column=5,row=0)
        
        self.GetSignalDataButton = tkinter.Button(self.buttonFrame,text="Get Sig Data",command=self.canipy.tx.signal_info)
        self.GetSignalDataButton.grid(column=6,row=0)

        self.MuteButton = tkinter.Button(self.buttonFrame,text="Mute",command=self.canipy.tx.mute)       
        self.MuteButton.grid(column=7,row=0)

        self.clockOnButton = tkinter.Button(self.buttonFrame,text="Clock On",command=lambda:self.canipy.tx.clock_mon(True))       
        self.clockOnButton.grid(column=8,row=0)

        # channel number 
        self.chEntry = tkinter.Entry(self.buttonFrame)
        self.chEntry.grid(column=0,row=1)
        self.chEntry.insert(tkinter.END, "1")

        self.SetDirectDevice = tkinter.Button(self.buttonFrame,text="Direct",command=self.set_direct_device)
        self.SetDirectDevice.grid(column=1,row=1)

        self.SetWcDevice = tkinter.Button(self.buttonFrame,text="WX Certified",command=self.set_wc_device)
        self.SetWcDevice.grid(column=2,row=1)

        self.powerOffButton = tkinter.Button(self.buttonFrame,text="Power Off",command=lambda:self.canipy.tx.power_down(pwr_sav=True))       
        self.powerOffButton.grid(column=3,row=1)

        self.getChInfoButton = tkinter.Button(self.buttonFrame,text="Ch Info",command=self.get_channel_info)       
        self.getChInfoButton.grid(column=4,row=1)

        self.extChInfoButton = tkinter.Button(self.buttonFrame,text="Ext Ch Info",command=self.get_extended_channel_info)       
        self.extChInfoButton.grid(column=5,row=1)

        self.sigMonButton = tkinter.Button(self.buttonFrame,text="Watch Sig",command=self.canipy.tx.sigmon_enable)       
        self.sigMonButton.grid(column=6,row=1)

        self.UnmuteButton = tkinter.Button(self.buttonFrame,text="Unmute",command=self.canipy.tx.unmute)       
        self.UnmuteButton.grid(column=7,row=1)
        
        self.clockOffButton = tkinter.Button(self.buttonFrame,text="Clock Off",command=lambda:self.canipy.tx.clock_mon(False))       
        self.clockOffButton.grid(column=8,row=1)
        
        # Buttons used during debug
        #
        # self.wxFwVerButton = tkinter.Button(self.buttonFrame,text="WX FirmVer",command=self.canipy.wx.firm_ver)       
        # self.wxFwVerButton.grid(column=9,row=0)
        # self.wxPingButton = tkinter.Button(self.buttonFrame,text="WX Ping",command=self.canipy.wx.ping)       
        # self.wxPingButton.grid(column=9,row=1)

        self.buttonFrame.grid(column=0, row=0)
        
        self.resizable(False,False)
        self.update()
        self.geometry(self.geometry())
    
    def change_channel(self):
        channel = int(self.chEntry.get())
        self.canipy.tx.change_channel(channel)

    def get_channel_info(self):
        channel = int(self.chEntry.get())
        self.canipy.tx.channel_info(channel)
        
    def get_extended_channel_info(self):
        channel = int(self.chEntry.get())
        self.canipy.tx.ext_info(channel)

    def open_com_port(self, baud:int=9600):
        # Close com if any open
        if self.canipy.serial_conn is not None: self.canipy.close()
        # get com port
        com_port = self.comEntry.get()
        print(f"Connect to {com_port} ({baud})")
        self.canipy.open(port=com_port, baud=baud)

    def set_pcr_device(self):
        print("Device set to PCR")
        self.open_com_port()
    
    def set_direct_device(self):
        self.set_pcr_device()
        print("Sending Direct enable commands")
        self.canipy.dx.enable()

    def set_wx_device(self):
        print("Device set to WX (Portable)")
        self.open_com_port(baud=38400)

    def set_wc_device(self):
        print("Device set to WX (Certified)")
        self.open_com_port(baud=115200)
        
if __name__ == "__main__":
    app = canipy_tk(None)
    app.title('CaniPy')
    app.mainloop()
        
              
        
        
