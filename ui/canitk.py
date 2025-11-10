import serial.tools.list_ports

from tkinter import Tk, StringVar, BooleanVar, IntVar, Menu, Frame, Text, END, messagebox, ttk

from utils import CaniPy

from .uithread import InterfaceThread
from .uiprep import InterfacePrep
from .uiwx import InterfaceWX

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

        # handlers
        self.uithread = InterfaceThread(self)
        self.uiprep = InterfacePrep(self)
        self.uiwx = InterfaceWX(self)

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
        self.uiprep.prep()
        
        self.resizable(False,False)
        self.update()
        #self.geometry(self.geometry())

        self.uithread.update()
    
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
