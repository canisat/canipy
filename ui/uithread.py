from tkinter import StringVar
from datetime import datetime, timezone, timedelta

class InterfaceThread:
    def __init__(self, parent):
        self.parent = parent

        # Marquee checks
        # Run ticker at half clock
        self.tickerThrottle = False
        # Buffer for comparing
        self.tickerBuffer = ""
    
    def update(self):
        if not self.parent.winfo_exists(): return

        # Populate only when connection is up
        if self.parent.canipy.serial_conn is not None:
            # update clock if set
            if self.parent.canipy.sat_datetime > datetime(1900,1,1,tzinfo=timezone.utc):
                curtime = self.parent.canipy.sat_datetime.astimezone(
                    timezone(
                        timedelta(
                            hours=self.parent.timezoneOptions[
                                self.parent.tzGuiVar.get()
                            ] + self.parent.dstToggle.get()
                        )
                    )
                )
                if self.parent.milclockToggle.get():
                    hfmt = curtime.strftime("%H:%M")
                else:
                    # platform agnostic approach for 12h
                    hfmt = curtime.strftime("%I:%M").lstrip("0")
                self.parent.labelFrame.config(
                    text=hfmt
                )
            for attr, meta in self.parent.labelVars.items():
                new_label = ""
                match attr:
                    case "signal":
                        sat = self.parent.canipy.sig_strength
                        ter = self.parent.canipy.ter_strength
                        # pick the strongest signal, unless sat is 0 and ter is 1
                        # as terrestrial strength indicator is rather loose
                        if sat == 0 and ter == 1:
                            sigpwr = 0
                        else:
                            sigpwr = max(sat,ter)
                        # Not the prettiest..
                        # new_label += f"""SAT {'[]'*self.parent.canipy.sig_strength+'  '*(
                        #     3-self.parent.canipy.sig_strength
                        # ) if self.parent.canipy.sig_strength > 0 else 'X   '} """
                        # new_label += "TER "
                        new_label += "T"
                        # Report signal if antenna is connected
                        if self.parent.canipy.ant_strength > 0:
                            new_label += f" {'[]'*sigpwr}"
                    case "ticker":
                        # If there's ticker data at all
                        # Otherwise if remnant marquee, clear it
                        if self.parent.canipy.ticker:
                            self.ticker(meta["var"])
                        elif meta["var"].get():
                            meta["var"].set("")
                    case _:
                        new_label += f"{getattr(self.parent.canipy,attr,'')}"
                # only update if value changed
                # less expensive doing so.
                # Disregard marquee as that's updated externally
                if attr != "ticker":
                    if meta["var"].get() != f"{new_label}":
                        meta["var"].set(f"{new_label}")

        # recursive loop
        # set to 100 so it doesnt chew cpu time..
        self.parent.after(100,self.update)
    
    def ticker(self, marquee:StringVar):
            # If marquee is empty or ticker updated, populate
            if not marquee.get() or (self.tickerBuffer != self.parent.canipy.ticker):
                marquee.set(self.parent.canipy.ticker)
                # buffer it
                self.tickerBuffer = self.parent.canipy.ticker
                # Pad at least up to 96
                if len(marquee.get()) < 96:
                    marquee.set(
                        marquee.get()+ " " * (
                            96 - len(marquee.get()) % 96 + 3
                        )
                    )
            # Run ticker at half speed
            if self.tickerThrottle:
                marquee.set(
                    marquee.get()[1:]+marquee.get()[0]
                )
                self.tickerThrottle = False
            else:
                self.tickerThrottle = True
