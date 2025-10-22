from tkinter import *
from tkinter import messagebox

from utils import CaniPy

class canipy_tk(Tk):  
    def __init__(self,parent):
        self.canipy = CaniPy(gui=self)

        Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

    @staticmethod
    def infobox(msg):
        messagebox.showinfo("CaniPy",msg)

    @staticmethod
    def warnbox(msg):
        messagebox.showwarning("CaniPy",msg)

    @staticmethod
    def errorbox(msg):
        messagebox.showerror("CaniPy",msg)

    def initialize(self):
        self.grid()
        
        # frame for command buttons
        self.buttonFrame = Frame(self.parent)
        
        # field for com port 
        self.comEntry = Entry(self.buttonFrame)
        self.comEntry.grid(column=0,row=0)
        self.comEntry.insert(END, "COM3")  #self.comEntry.set("COM3")
        
        self.SetPcrDevice = Button(self.buttonFrame,text="PCR",command=self.open_com_port)
        self.SetPcrDevice.grid(column=1,row=0)

        self.SetWxDevice = Button(self.buttonFrame,text="WX Portable",command=lambda:self.open_com_port(baud=38400))
        self.SetWxDevice.grid(column=2,row=0)
        
        self.powerOnButton = Button(self.buttonFrame,text="Power On",command=self.canipy.tx.power_up)       
        self.powerOnButton.grid(column=3,row=0)
        
        self.changeChannelButton = Button(self.buttonFrame,text="Change Ch",command=self.change_channel)       
        self.changeChannelButton.grid(column=4,row=0)
        
        self.getRadioIDButton = Button(self.buttonFrame,text="Get Radio ID",command=self.canipy.tx.get_radioid)       
        self.getRadioIDButton.grid(column=5,row=0)
        
        self.GetSignalDataButton = Button(self.buttonFrame,text="Get Sig Data",command=self.canipy.tx.signal_info)
        self.GetSignalDataButton.grid(column=6,row=0)

        self.MuteButton = Button(self.buttonFrame,text="Mute",command=self.canipy.tx.mute)       
        self.MuteButton.grid(column=7,row=0)

        self.clockOnButton = Button(self.buttonFrame,text="Clock On",command=lambda:self.canipy.tx.clock_mon(True))       
        self.clockOnButton.grid(column=8,row=0)

        # channel number 
        self.chEntry = Entry(self.buttonFrame)
        self.chEntry.grid(column=0,row=1)
        self.chEntry.insert(END, "1")

        self.SetDirectDevice = Button(self.buttonFrame,text="Direct",command=self.set_direct_device)
        self.SetDirectDevice.grid(column=1,row=1)

        self.SetWcDevice = Button(self.buttonFrame,text="WX Certified",command=lambda:self.open_com_port(baud=115200))
        self.SetWcDevice.grid(column=2,row=1)

        self.powerOffButton = Button(self.buttonFrame,text="Power Off",command=lambda:self.canipy.tx.power_down(pwr_sav=True))       
        self.powerOffButton.grid(column=3,row=1)

        self.getChInfoButton = Button(self.buttonFrame,text="Ch Info",command=self.get_channel_info)       
        self.getChInfoButton.grid(column=4,row=1)

        self.extChInfoButton = Button(self.buttonFrame,text="Ext Ch Info",command=self.get_extended_channel_info)       
        self.extChInfoButton.grid(column=5,row=1)

        self.sigMonButton = Button(self.buttonFrame,text="Watch Sig",command=self.canipy.tx.sigmon_enable)       
        self.sigMonButton.grid(column=6,row=1)

        self.UnmuteButton = Button(self.buttonFrame,text="Unmute",command=self.canipy.tx.unmute)       
        self.UnmuteButton.grid(column=7,row=1)
        
        self.clockOffButton = Button(self.buttonFrame,text="Clock Off",command=lambda:self.canipy.tx.clock_mon(False))       
        self.clockOffButton.grid(column=8,row=1)
        
        # Buttons used during debug
        #
        # self.wxFwVerButton = Button(self.buttonFrame,text="WX FirmVer",command=self.canipy.wx.firm_ver)       
        # self.wxFwVerButton.grid(column=9,row=0)
        # self.wxPingButton = Button(self.buttonFrame,text="WX Ping",command=self.canipy.wx.ping)       
        # self.wxPingButton.grid(column=9,row=1)

        self.buttonFrame.grid(column=0, row=0)
        
        # frame for labels
        self.labelFrame = Frame(self.parent)
        self.chnum_label = Label(self.labelFrame,text=f"Ch Num: {self.canipy.ch_num}")
        self.chnum_label.grid(column=0,row=0,sticky="w")
        self.chsid_label = Label(self.labelFrame,text=f"Ch SID: {self.canipy.ch_sid}")
        self.chsid_label.grid(column=0,row=1,sticky="w")
        self.chname_label = Label(self.labelFrame,text=f"Ch Name: {self.canipy.ch_name}")
        self.chname_label.grid(column=0,row=2,sticky="w")
        self.line1_label = Label(self.labelFrame,text=f"Line1: {self.canipy.artist_name}")
        self.line1_label.grid(column=0,row=3,sticky="w")
        self.line2_label = Label(self.labelFrame,text=f"Line2: {self.canipy.title_name}")
        self.line2_label.grid(column=0,row=4,sticky="w")
        self.catname_label = Label(self.labelFrame,text=f"Cat: {self.canipy.cat_name}")
        self.catname_label.grid(column=0,row=5,sticky="w")
        self.catid_label = Label(self.labelFrame,text=f"Cat ID: {self.canipy.cat_id}")
        self.catid_label.grid(column=0,row=6,sticky="w")
        self.sig_label = Label(self.labelFrame,text=f"Sat: {self.canipy.sig_strength}")
        self.sig_label.grid(column=0,row=7,sticky="w")
        self.ant_label = Label(self.labelFrame,text=f"Ant: {self.canipy.ant_strength}")
        self.ant_label.grid(column=0,row=8,sticky="w")
        self.ter_label = Label(self.labelFrame,text=f"Ter: {self.canipy.ter_strength}")
        self.ter_label.grid(column=0,row=9,sticky="w")
        self.time_label = Label(self.labelFrame,text=f"Time: {self.canipy.sat_datetime}")
        self.time_label.grid(column=0,row=10,sticky="w")
        self.radio_label = Label(self.labelFrame,text=f"Radio ID: {self.canipy.radio_id}")
        self.radio_label.grid(column=0,row=11,sticky="w")
        self.labelFrame.grid(column=0, row=1,sticky="w")
        
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
        self.canipy.open(port=com_port, baud=baud)
    
    def set_direct_device(self):
        self.open_com_port()
        if self.canipy.serial_conn is not None: self.canipy.dx.enable()
        
if __name__ == "__main__":
    app = canipy_tk(None)
    app.title('CaniPy')
    app.mainloop()
        
              
        
        
