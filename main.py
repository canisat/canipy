from tkinter import *
from tkinter import messagebox, ttk

from utils import CaniPy

class CaniTk(Tk):  
    def __init__(self):
        self.canipy = CaniPy(gui=self)

        super().__init__()

        self.title("CaniPy")

        # vars
        self.verboseToggle = BooleanVar(value=self.canipy.verbose)
        self.chGuiVar = IntVar(value=self.canipy.ch_num)

        # menu bar
        self.menuBar = Menu(self)
        self.config(menu=self.menuBar)

        # frames
        self.buttonFrame = Frame(self)
        self.labelFrame = ttk.LabelFrame(self,text="Debug Values")

        # input fields
        self.comEntry = Entry(self.buttonFrame)
        #self.chEntry = Entry(self.buttonFrame)
        self.chEntry = ttk.Spinbox(
            self.buttonFrame,
            from_=0,
            to=255,
            textvariable=self.chGuiVar,
            width=16
        )

        # label dict
        self.labelVars = {}

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
        #self.grid()
        
        # frame for command buttons
        self.buttonFrame.grid(column=0,row=0)
        
        # field for com port
        self.comEntry.grid(column=0,row=0)
        self.comEntry.insert(END,"COM3")  #self.comEntry.set("COM3")
        
        Button(self.buttonFrame,text="PCR",command=self.open_com_port).grid(column=1,row=0)
        Button(self.buttonFrame,text="WX Portable",command=lambda:self.open_com_port(baud=38400)).grid(column=2,row=0)
        Button(self.buttonFrame,text="Power On",command=self.canipy.tx.power_up).grid(column=3,row=0)
        Button(self.buttonFrame,text="Change Ch",command=lambda:self.canipy.tx.change_channel(int(self.chEntry.get()))).grid(column=4,row=0)
        Button(self.buttonFrame,text="Get Radio ID",command=self.canipy.tx.get_radioid).grid(column=5,row=0)
        Button(self.buttonFrame,text="Get Sig Data",command=self.canipy.tx.signal_info).grid(column=6,row=0)
        Button(self.buttonFrame,text="Mute",command=self.canipy.tx.mute).grid(column=7,row=0)
        Button(self.buttonFrame,text="Clock On",command=lambda:self.canipy.tx.clock_mon(True)).grid(column=8,row=0)

        # channel number
        self.chEntry.grid(column=0,row=1)
        #self.chEntry.insert(END,"1")

        Button(self.buttonFrame,text="Direct",command=self.set_direct_device).grid(column=1,row=1)
        Button(self.buttonFrame,text="WX Certified",command=lambda:self.open_com_port(baud=115200)).grid(column=2,row=1)
        Button(self.buttonFrame,text="Power Off",command=lambda:self.canipy.tx.power_down(pwr_sav=True)).grid(column=3,row=1)
        Button(self.buttonFrame,text="Ch Info",command=lambda:self.canipy.tx.channel_info(int(self.chEntry.get()))).grid(column=4,row=1)
        Button(self.buttonFrame,text="Ext Ch Info",command=lambda:self.canipy.tx.ext_info(int(self.chEntry.get()))).grid(column=5,row=1)
        Button(self.buttonFrame,text="Watch Sig",command=self.canipy.tx.sigmon_enable).grid(column=6,row=1)
        Button(self.buttonFrame,text="Unmute",command=self.canipy.tx.unmute).grid(column=7,row=1)
        Button(self.buttonFrame,text="Clock Off",command=lambda:self.canipy.tx.clock_mon(False)).grid(column=8,row=1)
        
        # Buttons used during debug
        #Button(self.buttonFrame,text="WX FirmVer",command=self.canipy.wx.firm_ver).grid(column=9,row=0)
        #Button(self.buttonFrame,text="WX Ping",command=self.canipy.wx.ping).grid(column=9,row=1)
        
        # frame for labels
        self.labelFrame.grid(column=0,row=1,columnspan=2)

        attrs = [
            "ch_num",
            "ch_sid",
            "ch_name",
            "artist_name",
            "title_name",
            "cat_name",
            "cat_id",
            "sig_strength",
            "ant_strength",
            "ter_strength",
            "sat_datetime",
            "radio_id"
        ]

        for i, attr in enumerate(attrs):
            var = StringVar()
            var.set(f"{attr}: {getattr(self.canipy,attr,'')}")
            Label(self.labelFrame,textvariable=var).grid(column=i//3,row=i%3,sticky="w")
            self.labelVars[attr] = var
        
        file_menu = Menu(self.menuBar,tearoff=False)
        file_menu.add_command(label="Exit",command=self.destroy,underline=1)
        self.menuBar.add_cascade(label="File",menu=file_menu,underline=0)

        debug_menu = Menu(self.menuBar,tearoff=False)
        debug_menu.add_checkbutton(
            label="Toggle Verbose Output",
            variable=self.verboseToggle,
            underline=7,
            command=lambda:setattr(self.canipy,"verbose",self.verboseToggle.get())
        )
        self.menuBar.add_cascade(label="Debug",menu=debug_menu,underline=0)

        help_menu = Menu(self.menuBar,tearoff=False)
        help_menu.add_command(
            label="About",
            command=lambda:messagebox.showinfo(
                "About",
                f"CaniPy - Version 0.25\n"
                f"SDARS hardware control in Python\n"
                f"Licensed under Apache 2.0\n"
                f"\n"
                f"This codebase is derived from PyXM by Timothy Canham\n"
                f"\n"
                f"Serial commands were documented from both current CaniSat "
                f"research and prior work conducted by Nick Sayer, the "
                f"linuXMPCR and Perl XM PCR projects, Hybrid Mobile "
                f"Technologies, and the defunct XM Fan forums.\n"
                f"\n"
                f"CaniSat, a non-profit initiative, and its incubator NetOtt "
                f"Solutions, LLC are not affiliated with either Sirius XM "
                f"Holdings Inc., Sirius XM Radio LLC, or any of its products, "
                f"partners, or subsidiaries. Sirius, XM, SiriusXM and all "
                f"related indicia are trademarks of Sirius XM Holdings Inc.\n"
                f"\n"
                f"The data products distributed in the service(s) are "
                f"intended to be supplemental and advisory per the provider. "
                f"It is not recommended for use in circumstances that "
                f"require immediate urgency to fulfill safety-critical work. "
                f"Both CaniSat and the service provider are not responsible "
                f"for errors and inaccuracies encountered when utilizing the "
                f"service data products.\n"
                f"\n"
                f"CaniSat does not condone or encourage the use of its "
                f"affiliated projects for unauthorized copying, duplication, "
                f"or distribution of copyrighted materials received through "
                f"the supported services. The end user is solely responsible "
                f"for ensuring their activities comply with applicable "
                f"copyright laws and service terms. Don't steal music.",
            ),
            underline=0
        )
        self.menuBar.add_cascade(label="Help",menu=help_menu,underline=0)
        
        self.resizable(False,False)
        self.update()
        #self.geometry(self.geometry())

        self.update_labels()
    
    def update_labels(self):
        if not self.winfo_exists(): return
        for attr, var in self.labelVars.items():
            var.set(f"{attr}: {getattr(self.canipy,attr,'')}")
        # recursive loop
        # 1 is more stable than either 0 or after_idle
        self.after(1,self.update_labels)

    def open_com_port(self, baud:int=9600):
        # Close com if any open
        if self.canipy.serial_conn is not None:
            self.canipy.close()
        # get com port
        com_port = self.comEntry.get()
        self.canipy.open(port=com_port, baud=baud)
        if self.canipy.serial_conn is not None:
            self.infobox(f"Connected to {com_port} ({baud} baud)")
    
    def set_direct_device(self):
        self.open_com_port()
        if self.canipy.serial_conn is not None:
            self.canipy.dx.enable()
        
if __name__ == "__main__": CaniTk().mainloop()
