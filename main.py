import serial.tools.list_ports

from tkinter import *
from tkinter import messagebox, ttk

import time

from utils import CaniPy

class CaniTk(Tk):  
    def __init__(self):
        super().__init__()

        self.title("CaniPy")

        self.baudOpts = {
            "PCR": 9600,
            "Direct": 0,
            "WX (Portable)": 38400,
            "WX (Certified)": 115200
        }

        # menu bar
        self.menuBar = Menu(self)
        self.config(menu=self.menuBar)

        # frames
        self.buttonFrame = Frame(self)
        self.labelFrame = ttk.LabelFrame(self,text="Display")
        
        # log elements
        self.logFrame = Frame(self)
        self.logField = Text(
            self.logFrame,
            width=64,
            height=12,
            wrap="word",
            state="disabled"
        )

        # canipy instance
        self.canipy = CaniPy(gui=self)

        # vars
        self.muteToggle = BooleanVar()
        self.sigmonToggle = BooleanVar(value=True)
        self.clockmonToggle = BooleanVar(value=True)
        self.wxToggle = BooleanVar()
        self.chGuiVar = IntVar(value=self.canipy.ch_num)
        self.labeldbgToggle = BooleanVar(value=True)
        self.verboseToggle = BooleanVar(value=self.canipy.verbose)
        self.radiodiagToggle = BooleanVar()
        self.wrgpsToggle = BooleanVar()

        # input fields
        #self.comEntry = Entry(self.buttonFrame)
        #self.chEntry = Entry(self.buttonFrame)
        #self.chEntry.set("Enter ch")
        self.chEntry = ttk.Spinbox(
            self.buttonFrame,
            from_=0,
            to=255,
            textvariable=self.chGuiVar,
            width=8
        )
        self.portList = [port.device for port in serial.tools.list_ports.comports()]
        self.portSelect = StringVar()
        if self.portList:
            # Default to first value in port list
            self.portSelect.set(self.portList[0])
        else:
            # Prompt user to enter port path if no list
            self.portSelect.set("Enter device here")
        self.hwtypeSelect = StringVar(value="Pick type to begin")

        # Labels for display
        self.labelVars = {
            "sig_strength":StringVar(),
            "ch_name":StringVar(),
            "artist_name":StringVar(),
            "sat_datetime":StringVar(),
            "ter_strength":StringVar(),
            "ch_num":StringVar(),
            "title_name":StringVar(),
            "radio_id":StringVar()
        }

        self.initialize()

    @staticmethod
    def infobox(msg:str):
        messagebox.showinfo("CaniPy",msg)

    @staticmethod
    def warnbox(msg:str):
        messagebox.showwarning("CaniPy",msg)

    @staticmethod
    def errorbox(msg:str):
        messagebox.showerror("CaniPy",msg)
    
    def logbox(self, msg:str):
        # enable, write, then disable and scroll
        self.logField.config(state="normal")
        # Check if empty; only newline if not the first element
        is_empty = self.logField.index("end-1c") == "1.0"
        self.logField.insert(END,("" if is_empty else "\n")+msg)
        self.logField.config(state="disabled")
        self.logField.see(END)

    def initialize(self):
        #self.grid()
        self.prep_menu()
        self.prep_buttons()
        self.prep_labels()
        self.prep_logfield()
        
        self.resizable(False,False)
        self.update()
        #self.geometry(self.geometry())

        self.update_labels()
    
    def prep_menu(self):
        # === File menu ===
        file_menu = Menu(self.menuBar,tearoff=False)
        file_menu.add_checkbutton(
            label="Mute",
            variable=self.muteToggle,
            command=lambda:self.canipy.tx.set_mute(self.muteToggle.get()),
            underline=0
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit",command=self.destroy,underline=1)
        self.menuBar.add_cascade(label="File",menu=file_menu,underline=0)

        # === Tools menu ===
        tools_menu = Menu(self.menuBar,tearoff=False)
        # Data
        tools_menu.add_checkbutton(
            label="Toggle WX data download",
            variable=self.wxToggle,
            command=self.wx_sequence,
            underline=7
        )
        tools_menu.add_checkbutton(
            label="Toggle WR GPS module",
            variable=self.wrgpsToggle,
            command=lambda:self.canipy.wx.wrgps_conn(self.wrgpsToggle.get()),
            underline=10
        )
        # === End tools menu ===
        self.menuBar.add_cascade(label="Tools",menu=tools_menu,underline=0)

        # === Debug menu ===
        debug_menu = Menu(self.menuBar,tearoff=False)
        # Fetch menu
        fetch_menu = Menu(debug_menu, tearoff=0)
        fetch_menu.add_command(
            label="Radio ID",
            command=self.canipy.tx.get_radioid,
            underline=0
        )
        fetch_menu.add_command(
            label="Firmware",
            command=self.canipy.tx.firm_ver,
            underline=0
        )
        fetch_menu.add_separator()
        fetch_menu.add_command(
            label="Selected channel",
            command=lambda:self.canipy.tx.channel_info(
                self.chEntry.get()
            ),
            underline=9
        )
        fetch_menu.add_command(
            label="Extended channel",
            command=lambda:self.canipy.tx.ext_info(
                self.chEntry.get()
            ),
            underline=0
        )
        fetch_menu.add_command(
            label="Signal",
            command=self.canipy.tx.signal_info,
            underline=0
        )
        fetch_menu.add_separator()
        # WX specific debug
        wxfetch_menu = Menu(fetch_menu, tearoff=0)
        wxfetch_menu.add_command(
            label="Ping",
            command=self.canipy.wx.ping,
            underline=0
        )
        wxfetch_menu.add_command(
            label="Data RX version",
            command=self.canipy.wx.firm_ver,
            underline=0
        )
        # end wx menu
        fetch_menu.add_cascade(label="WX",menu=wxfetch_menu,underline=0)
        # end of fetch
        debug_menu.add_cascade(label="Fetch info now",menu=fetch_menu,underline=0)
        # Debug monitoring menu
        mond_menu = Menu(debug_menu, tearoff=0)
        mond_menu.add_checkbutton(
            label="Radio diag",
            variable=self.radiodiagToggle,
            command=lambda:self.canipy.tx.diag_mon(self.radiodiagToggle.get()),
            underline=9
        )
        mond_menu.add_separator()
        mond_menu.add_command(
            label="Selected channel",
            command=lambda:self.canipy.tx.chan_mon(
                self.chEntry.get()
            ),
            underline=9
        )
        mond_menu.add_separator()
        mond_menu.add_checkbutton(
            label="Date/time",
            variable=self.clockmonToggle,
            command=lambda:self.canipy.tx.clock_mon(self.clockmonToggle.get()),
            underline=0
        )
        mond_menu.add_checkbutton(
            label="Signal",
            variable=self.sigmonToggle,
            command=lambda:self.canipy.tx.signal_mon(self.sigmonToggle.get()),
            underline=0
        )
        debug_menu.add_cascade(label="Debug Monitor",menu=mond_menu,underline=6)
        # Rest of debug
        debug_menu.add_separator()
        debug_menu.add_checkbutton(
            label="Toggle label display",
            variable=self.labeldbgToggle,
            command=lambda:self.labelFrame.grid() if self.labeldbgToggle.get() else self.labelFrame.grid_remove(),
            underline=7
        )
        debug_menu.add_checkbutton(
            label="Toggle verbose output",
            variable=self.verboseToggle,
            command=self.toggle_logfield,
            underline=7
        )
        debug_menu.add_separator()
        debug_menu.add_command(
            label="Clear verbose log",
            command=self.clear_logfield,
            underline=0
        )
        # End of debug menu
        self.menuBar.add_cascade(label="Debug",menu=debug_menu,underline=0)

        # Help menu
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

    def prep_buttons(self):
        # frame for command buttons
        self.buttonFrame.grid(column=0,row=0)

        # field for com port
        port_combo = ttk.Combobox(
            self.buttonFrame,
            textvariable=self.portSelect,
            values=self.portList,
            width=16
        )
        port_combo.grid(column=0,row=0)

        # self.comEntry.grid(column=0,row=0)
        # self.comEntry.insert(END,"COM3")
        #self.comEntry.set("COM3")

        hwtype_combo = ttk.Combobox(
            self.buttonFrame,
            textvariable=self.hwtypeSelect,
            values=list(self.baudOpts.keys()),
            state="readonly",
            width=16
        )
        hwtype_combo.grid(column=0,row=1)
        hwtype_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self.open_com_port(
                self.baudOpts[self.hwtypeSelect.get()]
            )
        )

        Label(
            self.buttonFrame,
            text="Channel"
        ).grid(column=1,row=0)

        Button(
            self.buttonFrame,
            text=">",
            height=2,
            command=lambda:self.canipy.tx.change_channel(
                int(self.chEntry.get())
            )
        ).grid(column=2,row=0,rowspan=2)

        # channel number
        self.chEntry.grid(column=1,row=1)
        #self.chEntry.insert(END,"1")
        
        # Buttons used during debug
        #Button(self.buttonFrame,text="WX FirmVer",command=self.canipy.wx.firm_ver).grid(column=9,row=0)
        #Button(self.buttonFrame,text="WX Ping",command=self.canipy.wx.ping).grid(column=9,row=1)

    def prep_labels(self):
        # frame for labels
        self.labelFrame.grid(column=0,row=1)

        for i, (attr, var) in enumerate(self.labelVars.items()):
            #var.set(f"{getattr(self.canipy,attr,'')}")
            Label(self.labelFrame,textvariable=var).grid(
                column=i//4,row=i%4,sticky=("e" if i//4 else "w")
            )

        # Remove if not enabled by default
        if not self.labeldbgToggle.get(): self.labelFrame.grid_remove()
    
    def prep_logfield(self):
        self.logFrame.grid(column=0,row=2)
        self.logField.grid(column=0,row=0)
        if not self.verboseToggle.get():
            self.logFrame.grid_remove()

    def update_labels(self):
        if not self.winfo_exists(): return

        for attr, var in self.labelVars.items():
            new_val = getattr(self.canipy,attr,"")
            new_label = ""
            match attr:
                case "sig_strength" | "ter_strength":
                    new_label += "SAT " if attr == "sig_strength" else "TER "
                    if any(x < 0 for x in (new_val, self.canipy.ant_strength)):
                        new_label += "X"
                    else:
                        new_label += str(new_val)
                case "sat_datetime":
                    new_label += f"{new_val.strftime('%H:%M')} UTC"
                case _:
                    new_label += str(new_val)
            # only update if value changed
            # less expensive doing so
            if var.get() != f"{new_label}":
                var.set(f"{new_label}")

        # recursive loop
        # set to 100 so it doesnt chew cpu time..
        self.after(100,self.update_labels)
    
    def toggle_logfield(self):
        self.canipy.verbose = self.verboseToggle.get()
        self.logFrame.grid() if self.verboseToggle.get() else self.logFrame.grid_remove()
    
    def clear_logfield(self):
        self.logField.config(state="normal")
        self.logField.delete("1.0",END)
        self.logField.config(state="disabled")

    def open_com_port(self, baud:int=9600):
        # Close com if any open
        if self.canipy.serial_conn is not None:
            self.canipy.close()
        # get com port
        com_port = self.portSelect.get()
        # If baud provided is 0, then it's direct
        is_direct = not baud
        if is_direct: baud = 9600
        # open connection
        self.canipy.open(port=com_port, baud=baud)
        if self.canipy.serial_conn is not None:
            self.infobox(f"Connected to {com_port} ({baud} baud)")
            if is_direct:
                self.canipy.dx.enable()
            else:
                self.canipy.tx.power_up()

    def wx_sequence(self):
        # Check if we're using a data receiver
        if self.canipy.baud_rate not in (38400, 115200) or self.canipy.serial_conn is None:
            self.wxToggle.set(False)
            self.errorbox("A weather data receiver is required to use this feature")
            return
        # Begin data
        if self.wxToggle.get():
            # Indicate we're in data mode
            self.canipy.data_in_use = True
            # Change to data service
            self.canipy.tx.channel_cancel(0xf0, True)
            time.sleep(1)
            self.canipy.tx.change_channel(0xf0, True, True)
            time.sleep(1)
            # Define products
            data_products = [
                0x0A,
                0xE6,
                0xE7,
                0xE8,
                0xEA,
                0xEB,
                0xEC,
                0xED,
                0xEE
            ]
            # Listen for data products
            for pid in data_products:
                self.canipy.wx.set_datachan(pid)
                time.sleep(0.5)
        else:
            # Sometimes 4F may linger unless radio is shut off first...
            #self.canipy.data_in_use = False
            # Halt all data download
            self.canipy.wx.data_stop()
        
if __name__ == "__main__": CaniTk().mainloop()
