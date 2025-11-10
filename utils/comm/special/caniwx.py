import os
from datetime import datetime

class CaniWX:
    """
    Functions related to data commands, notably to weather data receivers.

    Attributes:
        parent (CaniPy): A main CaniPy instance that this script will support.
    
    Lambda:
        data_stop(): Instructs the radio to halt data RX.
    """
    def __init__(self, parent:"CaniPy"):
        self.parent = parent

        self.data_stop = lambda: self.set_datachan(0xFF, True, True)

    @staticmethod
    def data_sum(data:bytes) -> int:
        """
        Computes the CRC sum of provided data from a frame for comparing.
        The implementation used is 16-bit Genibus.
        Start with all on, polynomial of 0x1021, then XOR with all on for output.
        reveng.sourceforge.io/crc-catalogue/16.htm#crc.cat.crc-16-genibus

        Example:
            Provided with 4 bytes "AB CD 12 34", the
            resulting Genibus sum is 0xF836.

        Args:
            data (bytes): The data to calculate the checksum with.

        Returns:
            int: Provides with the resulting sum.
        """
        datasum = 0xFFFF  # Begin with all bits as 1
        # For each byte
        for byte in data:
            # XOR assign to upper half
            datasum ^= (byte << 8)
            # For each bit
            for _ in range(8):
                # Is the sum's biggest bit currently 1?
                if datasum & 0x8000:
                    # Shift left and XOR with polynomial
                    datasum = ((datasum << 1) ^ 0x1021) & 0xFFFF
                else:
                    # Only shift left otherwise
                    datasum = (datasum << 1) & 0xFFFF
        # XOR to get the final result
        return datasum ^ 0xFFFF

    @staticmethod
    def write_data(sid:int, frame:int, data:bytes, crc_sum:int):
        """
        Stores the provided data to a file on the system.

        Example:
            For data from SID 230, frame A1, with sum ABCD,
            on midnight 2025 January 1, it will be stored in
            "data/230/a1_250101000000abcd.bin".

        Args:
            sid (int): The service ID where the data originated from.
            frame (int): The frame number of the corresponding data.
            data (bytes): The downloaded data to store.
            crc_sum (int): Appends the sum as an identifier for the file.
        """
        path = f"data/{sid}"
        file = f"{frame:03}_{datetime.now().strftime('%y%m%d%H%M%S')}{crc_sum:04x}.bin"
        if not os.path.exists(path):
            os.makedirs(path)
        with open(path+"/"+file, "wb") as file:
            file.write(data)

    def set_datachan(self, sid:int, datflagone:bool=False, datflagtwo:bool=False) -> bytes:
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
        # TODO: What are those two flags all about?
        if sid not in range(256):
            self.parent.errorprint("Invalid channel value")
            return b""
        if self.parent.verbose:
            self.parent.logprint(f"WX - Preparing for SID {sid}")
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
        if self.parent.verbose:
            self.parent.logprint("WX - Ping")
        return self.parent.tx.send(bytes([0x4A, 0x43]))

    def firm_ver(self) -> bytes:
        """
        Prompts the radio to report data receiver firmware version.

        Example:
            The radio will be provided with "4A 44".

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.parent.verbose:
            self.parent.logprint("WX - Check RX for data receiver version")
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
        # TODO: Figure out what WR GPS behavior is like
        if self.parent.verbose:
            self.parent.logprint("WR - Check RX for GPS module confirmation")
        return self.parent.tx.send(bytes([0x4B, 0x09, 0x00, 0x01 if toggle else 0x03]))

    def parse_data(self, payload:bytes, write:bool=False):
        """
        Rudimentary data implementation.
        Prints out information about the data, and passes it to be saved if prompted.

        Args:
            payload (bytes): A response, comprised as a set of bytes, to parse the information from.
            write (bool, optional): Write the contained data to disk after verify. Default set to false.
        """
        self.parent.logprint("=== DATA  INFO ===")
        self.parent.logprint(f"SID: {payload[2]}")
        self.parent.logprint(f"Frame: {payload[3]}")
        self.parent.logprint(f"Length: {payload[7]} bytes")
        # If CRC sums match, process it, otherwise report mismatch
        if (payload[11]|(payload[10]<<8)) == self.data_sum(payload[12:]):
            if write:
                self.write_data(
                    payload[2],
                    payload[3],
                    payload[12:],
                    payload[11]|(payload[10]<<8)
                )
            self.parent.logprint(
                f"Bitrate: "
                f"{(self.parent.thread.calc_bitrate(payload[7])/1000):.3f}"
                f"kbps"
            )
            if self.parent.verbose:
                self.parent.logprint(
                    f"Sum: {''.join(f'{b:02X}' for b in payload[10:12])}"
                )
                #print("===    DATA    ===")
                # Safely print out bare data
                #print(payload[12:].decode("utf-8", errors="replace"))
                #print("===    HEX!    ===")
                # Print out hex dump
                #print(" ".join(f'{b:02X}' for b in payload[12:]))
        else:
            self.parent.logprint("Sum mismatch!")
            if self.parent.verbose:
                self.parent.logprint(
                    f"Expected {''.join(f'{b:02X}' for b in payload[10:12])}, "
                    f"got {self.data_sum(payload[12:]):02X}"
                )
        self.parent.logprint("==================")
