import serial.tools.list_ports, time, configparser, os

from tkinter import *
from tkinter import messagebox, ttk

from utils import CaniPy

from .uithread import InterfaceThread

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

        # time stuff
        self.timezoneOptions = {
            "Atlantic": -4,
            "Eastern": -5,
            "Central": -6,
            "Mountain": -7,
            "Pacific": -8,
            "Alaska": -9,
            "Hawaii": -10,
            "UTC": 0
        }
        self.tzGuiVar = StringVar(value="Eastern")
        self.dstToggle = BooleanVar(value=False)
        self.milclockToggle = BooleanVar(value=False)

        # bools
        self.muteToggle = BooleanVar()
        self.sigmonToggle = BooleanVar(value=True)
        self.clockmonToggle = BooleanVar(value=True)
        self.wxToggle = BooleanVar()
        self.labelToggle = BooleanVar(value=True)
        self.logboxToggle = BooleanVar()
        self.logfileToggle = BooleanVar()
        self.radiodiagToggle = BooleanVar()
        self.wrgpsToggle = BooleanVar()

        # menu bar
        self.menuBar = Menu(self)
        self.config(menu=self.menuBar)

        # frames
        self.buttonFrame = Frame(self)
        self.labelFrame = ttk.LabelFrame(
            self,
            width=320,
            height=148,
            labelanchor="ne"
        )
        
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

        # post-flight vars
        self.chGuiVar = IntVar(value=self.canipy.ch_num)
        self.verboseToggle = BooleanVar(value=self.canipy.verbose)

        # input fields
        #self.chEntry = Entry(self.buttonFrame)
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
            self.portSelect.set("Enter port here")
        self.hwtypeSelect = StringVar(value="Pick type to begin")

        # Labels for display
        # with position values
        self.labelVars = {
            "signal":{
                "var":StringVar(value="T"),
                "row":0,
                "column":0,
                "anchor":"w",
                "columnspan":1
            },
            "cat_name":{
                "var":StringVar(),
                "row":0,
                "column":1,
                "anchor":"e",
                "columnspan":1
            },
            "ch_name":{
                "var":StringVar(value="CaniPy"),
                "row":1,
                "column":0,
                "anchor":"w",
                "columnspan":1
            },
            "ch_num":{
                "var":StringVar(value="Version 0.25"),
                "row":1,
                "column":1,
                "anchor":"e",
                "columnspan":1
            },
            "artist_name":{
                "var":StringVar(value="Waiting for radio"),
                "row":2,
                "column":0,
                "anchor":"e",
                "columnspan":2
            },
            "title_name":{
                "var":StringVar(),
                "row":3,
                "column":0,
                "anchor":"e",
                "columnspan":2
            },
            "ticker":{
                "var":StringVar(),
                "row":4,
                "column":0,
                "anchor":"n",
                "columnspan":2
            }
        }

        # Run before destroying window
        self.protocol("WM_DELETE_WINDOW",self.shut_down_com)

        self.uithread = InterfaceThread(self)

        self.initialize()

    def infobox(self, msg:str):
        if self.logfileToggle.get():
            # write to logfile if enabled
            with open("canipy.log", "a") as file:
                file.write(
                    f"[{self.canipy.sat_datetime}] [INF] {repr(msg)}\n"
                )
        messagebox.showinfo("CaniPy",msg)

    def warnbox(self, msg:str):
        if self.logfileToggle.get():
            # write to logfile if enabled
            with open("canipy.log", "a") as file:
                file.write(
                    f"[{self.canipy.sat_datetime}] [WRN] {repr(msg)}\n"
                )
        messagebox.showwarning("CaniPy",msg)

    def errorbox(self, msg:str):
        if self.logfileToggle.get():
            # write to logfile if enabled
            with open("canipy.log", "a") as file:
                file.write(
                    f"[{self.canipy.sat_datetime}] [ERR] {repr(msg)}\n"
                )
        messagebox.showerror("CaniPy",msg)
    
    def logbox(self, msg:str):
        if self.logfileToggle.get():
            # write to logfile if enabled
            with open("canipy.log", "a") as file:
                file.write(
                    f"[{self.canipy.sat_datetime}] [DBG] {repr(msg)}\n"
                )
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

        self.uithread.update()
    
    def prep_menu(self):
        # === File menu ===
        file_menu = Menu(self.menuBar,tearoff=0)
        file_menu.add_checkbutton(
            label="Mute",
            variable=self.muteToggle,
            command=lambda:self.canipy.tx.set_mute(self.muteToggle.get()),
            underline=0
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Power up",
            command=self.open_com_port,
            underline=6
        )
        file_menu.add_command(
            label="Power down",
            command=self.canipy.tx.power_down,
            underline=6
        )
        file_menu.add_separator()
        # Data
        wxtools_menu = Menu(file_menu, tearoff=0)
        wxtools_menu.add_checkbutton(
            label="Toggle data download",
            variable=self.wxToggle,
            command=self.wx_sequence,
            underline=7
        )
        wxtools_menu.add_checkbutton(
            label="Toggle GPS module",
            variable=self.wrgpsToggle,
            command=lambda:self.canipy.wx.wrgps_conn(self.wrgpsToggle.get()),
            underline=7
        )
        # end wx menu
        file_menu.add_cascade(label="WX",menu=wxtools_menu,underline=0)
        file_menu.add_separator()
        file_menu.add_command(label="Exit",command=self.destroy,underline=1)
        self.menuBar.add_cascade(label="File",menu=file_menu,underline=0)

        # preferences menu
        prefs_menu = Menu(self.menuBar,tearoff=0)
        # time settings
        tz_menu = Menu(prefs_menu,tearoff=0)
        tz_menu.add_checkbutton(
            label="Daylight savings",
            variable=self.dstToggle,
            underline=9
        )
        tz_menu.add_separator()
        tz_menu.add_checkbutton(
            label="24-hour display",
            variable=self.milclockToggle,
            underline=8
        )
        tz_menu.add_separator()
        for tz_name in self.timezoneOptions.keys():
            tz_menu.add_radiobutton(
                label=tz_name,
                variable=self.tzGuiVar,
                value=tz_name,
                command=lambda t=tz_name: self.tzGuiVar.set(t),
                underline=1 if tz_name == "Alaska" else 0
            )
        prefs_menu.add_cascade(label="Clock",menu=tz_menu,underline=0)
        # END prefs menu
        self.menuBar.add_cascade(label="Settings",menu=prefs_menu,underline=0)

        # === Tools menu ===
        tools_menu = Menu(self.menuBar,tearoff=0)
        # Fetch menu
        fetch_menu = Menu(tools_menu, tearoff=0)
        fetch_menu.add_command(
            label="Selected channel",
            command=lambda:self.canipy.tx.channel_info(
                int(self.chEntry.get())
            ),
            underline=9
        )
        fetch_menu.add_command(
            label="Extended channel",
            command=lambda:self.canipy.tx.ext_info(
                int(self.chEntry.get())
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
        # end wx menu
        fetch_menu.add_cascade(label="WX",menu=wxfetch_menu,underline=0)
        # end of fetch
        tools_menu.add_cascade(label="Fetch info now",menu=fetch_menu,underline=0)
        # Debug monitoring menu
        mond_menu = Menu(tools_menu, tearoff=0)
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
                int(self.chEntry.get())
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
        tools_menu.add_cascade(label="Monitor",menu=mond_menu,underline=0)
        # Rest of tools
        tools_menu.add_separator()
        tools_menu.add_checkbutton(
            label="Toggle verbose logging",
            variable=self.verboseToggle,
            command=lambda:setattr(self.canipy,"verbose",self.verboseToggle.get()),
            underline=7
        )
        tools_menu.add_checkbutton(
            label="Toggle log file output",
            variable=self.logfileToggle,
            underline=16
        )
        tools_menu.add_separator()
        tools_menu.add_checkbutton(
            label="Show log box",
            variable=self.logboxToggle,
            command=lambda:self.logFrame.grid() if self.logboxToggle.get() else self.logFrame.grid_remove(),
            underline=9
        )
        tools_menu.add_command(
            label="Clear log box",
            command=self.clear_logfield,
            underline=0
        )
        tools_menu.add_separator()
        tools_menu.add_checkbutton(
            label="Show display",
            variable=self.labelToggle,
            command=lambda:self.labelFrame.grid() if self.labelToggle.get() else self.labelFrame.grid_remove(),
            underline=5
        )
        tools_menu.add_command(
            label="Feed money to stock ticker",
            command=lambda:setattr(
                self.canipy,
                "ticker",
                self.canipy.ticker+"$"
            ),
            underline=20
        )
        # === End tools menu ===
        self.menuBar.add_cascade(label="Toolbox",menu=tools_menu,underline=0)

        # Help menu
        help_menu = Menu(self.menuBar,tearoff=0)
        help_menu.add_command(
            label="Radio ID",
            command=self.canipy.tx.get_radioid,
            underline=6
        )
        help_menu.add_command(
            label="Firmware info",
            command=self.canipy.tx.firm_ver,
            underline=0
        )
        help_menu.add_separator()
        # WX specific debug
        wxhelp_menu = Menu(help_menu, tearoff=0)
        wxhelp_menu.add_command(
            label="Data RX version",
            command=self.canipy.wx.firm_ver,
            underline=0
        )
        # end wx menu
        help_menu.add_cascade(label="WX",menu=wxhelp_menu,underline=0)        
        help_menu.add_separator()
        help_menu.add_command(
            label="About CaniPy",
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
            lambda e: self.open_com_port()
        )
        
        Label(
            self.buttonFrame,
            text="Port"
        ).grid(column=1,row=0,sticky="w")
        Label(
            self.buttonFrame,
            text="Device"
        ).grid(column=1,row=1,sticky="w")

        Frame(
            self.buttonFrame,
            width=55
        ).grid(column=2,row=0,rowspan=2)

        Label(
            self.buttonFrame,
            text="Channel"
        ).grid(column=3,row=0)
        # channel number
        self.chEntry.grid(column=3,row=1)
        #self.chEntry.insert(END,"1")

        Button(
            self.buttonFrame,
            text="Enter",
            width=4,
            height=2,
            command=lambda:self.canipy.tx.change_channel(
                int(self.chEntry.get())
            )
        ).grid(column=4,row=0,rowspan=2)

    def prep_labels(self):
        # frame for labels
        self.labelFrame.grid(column=0,row=1)
        self.labelFrame.grid_propagate(False)

        for _, meta in self.labelVars.items():
            lbl = Label(
                self.labelFrame,
                textvariable=meta["var"],
                anchor=meta["anchor"]
            )
            lbl.grid(
                row=meta["row"],
                column=meta["column"],
                sticky="ew",
                columnspan=meta["columnspan"]
            )
            lbl.config(font=("TkDefaultFont",12))
            match meta["row"]:
                case 1:
                    lbl.config(bg="black",fg="white")
                case 2:
                    lbl.config(font=("TkDefaultFont",16,"bold"))

        # Set weight for columns to even out the labels
        for c in range(2):
            self.labelFrame.columnconfigure(c,weight=1)

        # Remove if not enabled by default
        if not self.labelToggle.get(): self.labelFrame.grid_remove()
    
    def prep_logfield(self):
        self.logFrame.grid(column=0,row=2)
        self.logField.grid(column=0,row=0)
        if not self.logboxToggle.get():
            self.logFrame.grid_remove()
    
    def clear_logfield(self):
        self.logField.config(state="normal")
        self.logField.delete("1.0",END)
        self.logField.config(state="disabled")

    def open_com_port(self):
        # Stop if dropdown is still in placeholder
        if self.hwtypeSelect.get() not in self.baudOpts:
            self.errorbox("Please select a device type first")
            return
        # fetch baud rate
        baud = self.baudOpts[self.hwtypeSelect.get()]
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
                # Use enable instead of normal
                # powerup if device is direct
                self.canipy.dx.enable()
                return
            self.canipy.tx.power_up()

    def shut_down_com(self):
        if self.canipy.serial_conn is not None:
            self.canipy.tx.power_down()
        self.destroy()

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