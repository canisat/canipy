class InterfaceWX:
    def __init__(self, parent):
        self.parent = parent

    def sequence(self):
        # Check if we're using a data receiver
        if self.parent.canipy.baud_rate not in (38400, 115200) or self.parent.canipy.serial_conn is None:
            self.parent.wxToggle.set(False)
            self.parent.errorbox("A weather data receiver is required to use this feature")
            return
        # Begin data
        if self.parent.wxToggle.get():
            # Indicate we're in data mode
            self.parent.canipy.data_in_use = True
            # Change to data service
            self.parent.canipy.tx.channel_cancel(0xf0, True)
            time.sleep(1)
            self.parent.canipy.tx.change_channel(0xf0, True, True)
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
                self.parent.canipy.wx.set_datachan(pid)
                time.sleep(0.5)
        else:
            # Sometimes 4F may linger unless radio is shut off first...
            #self.parent.canipy.data_in_use = False
            # Halt all data download
            self.parent.canipy.wx.data_stop()
