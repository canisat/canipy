from tkinter import Menu, Label, Frame, Button, ttk, messagebox

class InterfacePrep:
    def __init__(self, parent):
        self.parent = parent
    
    def prep(self):
        self.prep_menu()
        self.prep_buttons()
        self.prep_labels()
        self.prep_logfield()

    def prep_menu(self):
        # === File menu ===
        file_menu = Menu(self.parent.menuBar,tearoff=0)
        file_menu.add_checkbutton(
            label="Mute",
            variable=self.parent.muteToggle,
            command=lambda:self.parent.canipy.tx.set_mute(self.parent.muteToggle.get()),
            underline=0
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Power up",
            command=self.parent.open_com_port,
            underline=6
        )
        file_menu.add_command(
            label="Power down",
            command=self.parent.canipy.tx.power_down,
            underline=6
        )
        file_menu.add_separator()
        # Data
        wxtools_menu = Menu(file_menu, tearoff=0)
        wxtools_menu.add_checkbutton(
            label="Toggle data download",
            variable=self.parent.wxToggle,
            command=self.parent.uiwx.sequence,
            underline=7
        )
        wxtools_menu.add_checkbutton(
            label="Toggle GPS module",
            variable=self.parent.wrgpsToggle,
            command=lambda:self.parent.canipy.wx.wrgps_conn(self.parent.wrgpsToggle.get()),
            underline=7
        )
        # end wx menu
        file_menu.add_cascade(label="WX",menu=wxtools_menu,underline=0)
        file_menu.add_separator()
        file_menu.add_command(label="Exit",command=self.parent.destroy,underline=1)
        self.parent.menuBar.add_cascade(label="File",menu=file_menu,underline=0)

        # preferences menu
        prefs_menu = Menu(self.parent.menuBar,tearoff=0)
        # time settings
        tz_menu = Menu(prefs_menu,tearoff=0)
        tz_menu.add_checkbutton(
            label="Daylight savings",
            variable=self.parent.dstToggle,
            command=self.parent.uicfg.save_file,
            underline=9
        )
        tz_menu.add_separator()
        tz_menu.add_checkbutton(
            label="24-hour display",
            variable=self.parent.milclockToggle,
            command=self.parent.uicfg.save_file,
            underline=8
        )
        tz_menu.add_separator()
        for tz_name in self.parent.timezoneOptions.keys():
            tz_menu.add_radiobutton(
                label=tz_name,
                variable=self.parent.tzGuiVar,
                value=tz_name,
                command=lambda t=tz_name: self.parent.uicfg.update_tz(t),
                underline=1 if tz_name == "Alaska" else 0
            )
        # end tz settings
        prefs_menu.add_cascade(label="Clock",menu=tz_menu,underline=0)
        # preset clear settings
        prere_menu = Menu(prefs_menu,tearoff=0)
        for preset in range(len(self.parent.chPresets)):
            prere_menu.add_command(
                label=str(preset+1),
                command=lambda p=preset: self.parent.uicfg.clear_preset(p),
                underline=0
            )
        prere_menu.add_separator()
        prere_menu.add_command(
            label="All",
            command=self.parent.uicfg.clear_all_presets,
            underline=0
        )
        # end preset
        prefs_menu.add_cascade(label="Clear preset",menu=prere_menu,underline=4)
        prefs_menu.add_separator()
        # DEBUG MENU
        prefdbg_menu = Menu(prefs_menu,tearoff=0)
        prefdbg_menu.add_checkbutton(
            label="Log file output",
            variable=self.parent.logfileToggle,
            command=self.parent.uicfg.save_file,
            underline=9
        )
        # yyyyeah, these won't autosave when toggled...
        # space is already taken by setattr, sorry.
        # closing ui or applying another setting will save anyway.
        prefdbg_menu.add_checkbutton(
            label="Verbose logging",
            variable=self.parent.verboseToggle,
            command=lambda:setattr(self.parent.canipy,"verbose",self.parent.verboseToggle.get()),
            underline=0
        )
        prefdbg_menu.add_checkbutton(
            label="Clock logging",
            variable=self.parent.clkdbgToggle,
            command=lambda:setattr(self.parent.canipy,"clock_logging",self.parent.clkdbgToggle.get()),
            underline=4
        )
        prefdbg_menu.add_checkbutton(
            label="Data logging",
            variable=self.parent.datdbgToggle,
            command=lambda:setattr(self.parent.canipy,"data_logging",self.parent.datdbgToggle.get()),
            underline=0
        )
        prefdbg_menu.add_separator()
        prefdbg_menu.add_checkbutton(
            label="Show log box",
            variable=self.parent.logboxToggle,
            command=lambda:self.parent.logFrame.grid() if self.parent.logboxToggle.get() else self.parent.logFrame.grid_remove(),
            underline=9
        )
        prefdbg_menu.add_command(
            label="Clear log box",
            command=self.parent.clear_logfield,
            underline=0
        )
        prefdbg_menu.add_separator()
        # Fetch menu
        fetch_menu = Menu(prefdbg_menu, tearoff=0)
        fetch_menu.add_command(
            label="Selected channel",
            command=lambda:self.parent.canipy.tx.channel_info(
                int(self.parent.chEntry.get())
            ),
            underline=9
        )
        fetch_menu.add_command(
            label="Extended channel",
            command=lambda:self.parent.canipy.tx.ext_info(
                int(self.parent.chEntry.get())
            ),
            underline=0
        )
        fetch_menu.add_command(
            label="Signal",
            command=self.parent.canipy.tx.signal_info,
            underline=0
        )
        fetch_menu.add_separator()
        # WX specific debug
        wxfetch_menu = Menu(fetch_menu, tearoff=0)
        wxfetch_menu.add_command(
            label="Ping",
            command=self.parent.canipy.wx.ping,
            underline=0
        )
        # end wx menu
        fetch_menu.add_cascade(label="WX",menu=wxfetch_menu,underline=0)
        # end of fetch
        prefdbg_menu.add_cascade(label="Fetch info now",menu=fetch_menu,underline=0)
        # Debug monitoring menu
        mond_menu = Menu(prefdbg_menu, tearoff=0)
        mond_menu.add_checkbutton(
            label="Radio diag",
            variable=self.parent.radiodiagToggle,
            command=lambda:self.parent.canipy.tx.diag_mon(self.parent.radiodiagToggle.get()),
            underline=9
        )
        mond_menu.add_separator()
        mond_menu.add_command(
            label="Selected channel",
            command=lambda:self.parent.canipy.tx.chan_mon(
                int(self.parent.chEntry.get())
            ),
            underline=9
        )
        mond_menu.add_command(
            label="Selected channel (Data override)",
            command=lambda:self.parent.canipy.tx.chan_mon(
                int(self.parent.chEntry.get()),
                mode_override=True
            ),
            underline=23
        )
        mond_menu.add_separator()
        mond_menu.add_checkbutton(
            label="Date/time",
            variable=self.parent.clockmonToggle,
            command=lambda:self.parent.canipy.tx.clock_mon(self.parent.clockmonToggle.get()),
            underline=0
        )
        mond_menu.add_checkbutton(
            label="Signal",
            variable=self.parent.sigmonToggle,
            command=lambda:self.parent.canipy.tx.signal_mon(self.parent.sigmonToggle.get()),
            underline=0
        )
        prefdbg_menu.add_cascade(label="Monitor",menu=mond_menu,underline=0)
        # Rest of tools
        prefdbg_menu.add_separator()
        prefdbg_menu.add_command(
            label="Populate ticker",
            command=lambda:setattr(
                self.parent.canipy,
                "ticker",
                self.parent.canipy.ticker+"#"
            ),
            underline=9
        )
        # END DEBUG
        prefs_menu.add_cascade(label="Advanced",menu=prefdbg_menu,underline=1)
        # END prefs menu
        self.parent.menuBar.add_cascade(label="Options",menu=prefs_menu,underline=0)

        # Help menu
        help_menu = Menu(self.parent.menuBar,tearoff=0)
        help_menu.add_command(
            label="Radio ID",
            command=self.parent.canipy.tx.get_radioid,
            underline=6
        )
        help_menu.add_command(
            label="Firmware info",
            command=self.parent.canipy.tx.firm_ver,
            underline=0
        )
        help_menu.add_separator()
        # WX specific debug
        wxhelp_menu = Menu(help_menu, tearoff=0)
        wxhelp_menu.add_command(
            label="Data RX version",
            command=self.parent.canipy.wx.firm_ver,
            underline=0
        )
        # end wx menu
        help_menu.add_cascade(label="WX",menu=wxhelp_menu,underline=0)        
        help_menu.add_separator()
        help_menu.add_command(
            label="About CaniPy",
            command=lambda:messagebox.showinfo(
                "About",
                f"CaniPy - Version 0.30\n"
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
        self.parent.menuBar.add_cascade(label="Help",menu=help_menu,underline=0)

    def prep_buttons(self):
        # frame for command buttons
        self.parent.buttonFrame.grid(column=0,row=0)

        # These are all arranged by tab order!
        # Row/Col assignments are gonna be a tad willy nilly

        # ch num box label
        Label(
            self.parent.buttonFrame,
            text="Channel"
        ).grid(column=0,row=0)
        # channel number
        self.parent.chEntry.grid(column=0,row=1)
        Button(
            self.parent.buttonFrame,
            text="Enter",
            width=4,
            height=2,
            command=lambda:self.parent.canipy.tx.change_channel(
                int(self.parent.chEntry.get())
            )
        ).grid(column=2,row=0,rowspan=2)

        # Preset buttons
        preset_btns = Frame(self.parent.buttonFrame)
        for num in range(len(self.parent.chPresets)):
            Button(
                preset_btns,
                text=num+1,
                command=lambda p=num:self.parent.canipy.tx.change_channel(
                    self.parent.chPresets[p].get()
                ) if self.parent.chPresets[p].get() > 0 else self.parent.uicfg.set_preset(
                    p,self.parent.canipy.ch_num
                )
            ).grid(column=num%3,row=num//3)
        preset_btns.grid(column=1,row=0,rowspan=2)

        # Combobox labels
        Label(
            self.parent.buttonFrame,
            text="Port"
        ).grid(column=3,row=0,sticky="e")
        Label(
            self.parent.buttonFrame,
            text="Device"
        ).grid(column=3,row=1,sticky="e")
        # field for com port
        port_combo = ttk.Combobox(
            self.parent.buttonFrame,
            textvariable=self.parent.portSelect,
            values=self.parent.portList,
            width=16
        )
        port_combo.grid(column=4,row=0)
        hwtype_combo = ttk.Combobox(
            self.parent.buttonFrame,
            textvariable=self.parent.hwtypeSelect,
            values=list(self.parent.baudOpts.keys()),
            state="readonly",
            width=16
        )
        hwtype_combo.grid(column=4,row=1)
        hwtype_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self.parent.open_com_port()
        )

    def prep_labels(self):
        # frame for labels
        self.parent.labelFrame.grid(column=0,row=1)
        self.parent.labelFrame.grid_propagate(False)

        for _, meta in self.parent.labelVars.items():
            lbl = Label(
                self.parent.labelFrame,
                textvariable=meta["var"],
                anchor=meta["anchor"]
            )
            lbl.grid(
                row=meta["row"],
                column=meta["column"],
                sticky="ew",
                columnspan=meta["columnspan"]
            )
            lbl.config(font=("TkDefaultFont",10))
            match meta["row"]:
                case 1:
                    lbl.config(bg="black",fg="white")
                case 2:
                    lbl.config(font=("TkDefaultFont",16,"bold"))
                case 3:
                    lbl.config(font=("TkDefaultFont",12))

        # Set weight for columns to even out the labels
        for c in range(2):
            self.parent.labelFrame.columnconfigure(c,weight=1)
    
    def prep_logfield(self):
        self.parent.logFrame.grid(column=0,row=2)
        self.parent.logField.grid(column=0,row=0)
        if not self.parent.logboxToggle.get():
            self.parent.logFrame.grid_remove()