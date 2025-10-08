class CaniWX:
    """
    Functions related to data commands, notably to weather data receivers.

    Attributes:
        parent (CaniPy): A main CaniPy instance that this script will support.
    
    Lambda:
        data_stop(): Instructs the radio to halt data RX.
    """
    # Functions will be moved here gradually
    def __init__(self, parent:"CaniPy"):
        self.parent = parent

        self.data_stop = lambda: self.change_datachan(0xFF, True, True)

    def change_datachan(self, sid:int, datflagone:bool=False, datflagtwo:bool=False) -> bytes:
        """
        Sets the specialized receiver to a data channel.

        Example:
            By default, if tuning to SID 240, the radio will be provided with
            "4A 10 F0 00 00" to prepare and begin data download.

        Args:
            sid (int): Service ID of the data channel.
            datflagone (bool, optional): Magic flag. Only ever seen enabled if SID is FF (255). Default to false.
            datflagtwo (bool, optional): Magic flag. Only ever seen enabled if SID is FF (255). Default to false.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if sid not in range(256):
            print("Invalid channel value")
            return b""
        if self.parent.verbose: print(f"WX - Preparing for SID {sid}")
        return self.parent.tx.send(bytes([0x4A, 0x10, sid, datflagone, datflagtwo]))

    def ping(self) -> bytes:
        """
        Sends a "ping" for the radio to answer back.
        A response of CA 43 hex is expected.

        Example:
            The radio will be provided with "4A 43".

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        print("WX - Ping")
        return self.parent.tx.send(bytes([0x4A, 0x43]))

    def firm_ver(self) -> bytes:
        """
        Prompts the radio to report data receiver firmware version.

        Example:
            The radio will be provided with "4A 44".

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.parent.verbose: print("WX - Check RX for data receiver version")
        return self.parent.tx.send(bytes([0x4A, 0x44]))

    def wrgps_conn(self, toggle:bool) -> bytes:
        """
        Prompts the radio to set the GPS receiver module state if equipped.
        This command will only work with later weather receivers!
        No idea what the radio would return either!

        Example:
            If "toggle" is True, the radio will be provided with
            "4B 09 00 01" to enable its embedded GPS module. If False,
            the last byte sent is "03" to disconnect the module.

        Args:
            toggle (bool): Prompt to enable or disable radio's GPS module.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.parent.verbose: print("WR - Check RX for GPS module confirmation")
        return self.parent.tx.send(bytes([0x4B, 0x09, 0x00, 0x01 if toggle else 0x03]))
