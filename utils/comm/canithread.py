import time, threading
from datetime import datetime

class CaniThread:
    """
    Threaded instance reading the port for responses from the radio.

    Attributes:
        parent (CaniPy): A main CaniPy instance that this script will support.
        thread_signal (threading.Event): Prompts the threaded function to halt.
        com_thread (threading.Thread): The actual thread entity looking for responeses.

        last_tick (datetime): Used for storing last datetime to calculate debug.
        last_bitrate (datetime): Used for storing last datetime to calculate bitrate.
        bitsize_count (int): Store the size of the bits received.
        curr_bitrate (int): The last reported bitrate.
    """
    def __init__(self, parent:"CaniPy"):
        self.parent = parent
        self.thread_signal = threading.Event()
        self.com_thread = None

        self.last_tick = datetime.min
        self.last_bitrate = datetime.min
        self.bitsize_count = 0
        self.curr_bitrate = 0

    def calc_delta(self) -> float:
        """
        Used for printing out TPS rate information by
        obtaining the delta, given the current datetime
        stamp and referencing a past value.

        Returns:
            float: The ticks per second based off the delta.
        """
        now = datetime.now()
        time_delta = (now - self.last_tick).total_seconds()
        self.last_tick = now
        return 1 / time_delta if time_delta > 0 else 0

    def calc_bitrate(self, size:int) -> int:
        """
        Used for printing out bits/sec information by
        obtaining the delta, given the current datetime
        stamp, bytes received, and checking if a second passed.

        Args:
            size (int): Size of reported packet in bytes.

        Returns:
            int: The bitrate based off what was accumulated.
        """
        now = datetime.now()
        self.bitsize_count += size*8 # Bytes * 8 gives bits
        if (now - self.last_bitrate).total_seconds() >= 1:
            self.curr_bitrate = self.bitsize_count
            self.bitsize_count = 0
            self.last_bitrate = now
            return self.curr_bitrate
        return self.curr_bitrate

    def start(self):
        """
        Starts the thread
        """
        if self.com_thread and self.com_thread.is_alive():
            if self.parent.verbose:
                self.parent.logprint("CaniThread already running")
            return
        self.thread_signal.clear()
        self.com_thread = threading.Thread(target=self.thread_read,name="CaniThread",daemon=True)
        # start com port read thread
        self.com_thread.start()
        if self.parent.verbose:
            self.parent.logprint("CaniThread started")

    def stop(self):
        """
        Stop thread upon window exit
        """
        self.thread_signal.set()
        if not self.com_thread:
            if self.parent.verbose:
                self.parent.logprint("CaniThread already stopped")
            return
        self.com_thread.join()
        self.com_thread = None
        if self.parent.verbose:
            self.parent.logprint("CaniThread stopped")

    def thread_read(self):
        """
        Main threaded instance, reading serial buffer and handing it over to RX.
        """
        # Keep calling the read method for the port
        while not self.thread_signal.is_set():
            buf = self.thread_buffer()
            if not buf: continue  # sure wish i was buff..
            self.parent.conductor.go(buf)

    def thread_buffer(self) -> bytes:
        """
        Reads from the serial connection, extracting payloads returned from the radio.

        Example:
            The current serial connection is read for any new commands.

        Returns:
            bytes: Returns the payload that was read.
        """
        if self.parent.serial_conn is None or not getattr(self.parent.serial_conn,"is_open",False):
            # wait for port to be connected
            time.sleep(1)
            return b""
            
        # read header 
        # first two bytes are 5AA5, like command
        # second two bytes are size.
        packet = b""
        read_so_far = 0
        while read_so_far < 5:
            # Because this is a threaded function, serial_conn can
            # change to None at ANY MOMENT, even if it clears the
            # check at the start of this function!
            # Best to handle exceptions to cater those edge cases.
            #if self.canipy.serial_conn is None or not self.canipy.serial_conn.is_open:
            try:
                chunk = self.parent.serial_conn.read(5-read_so_far)
            except Exception as e:
                if self.parent.verbose: (type(e))
                # wait for port to be connected
                time.sleep(1)
                return b""
            packet += chunk
            read_so_far += len(chunk)
            #print(f"{len(chunk)} {read_so_far}:")
            if self.thread_signal.is_set(): return b""
            
        if len(packet) != 5:
            self.parent.logprint("Unexpected header size")
            if self.parent.verbose:
                self.parent.logprint(f"Exp 5, got {len(packet)}")
            #print(packet)
            return b""
        # verify it is the header
        if packet[:2] != self.parent.header:
            self.parent.logprint("Header not found")
            if self.parent.verbose:
                self.parent.logprint(f"Received: {' '.join(f'{b:02X}' for b in packet[:2])}")
            #print(packet)
            return b""
        # Both of these do the same thing, but codebase
        # is to keep consistency with the more
        # biblically accurate bitwise operation...
        #size = packet[2]*256 + packet[3]
        size = (packet[2] << 8) | packet[3]
        # read the rest of the packet
        #if self.canipy.serial_conn is None or not self.canipy.serial_conn.is_open:
        try:
            rest_of_packet = self.parent.serial_conn.read(size+1)
        except Exception as e:
            if self.parent.verbose: (type(e))
            # wait for port to be connected
            time.sleep(1)
            return b""
        if len(rest_of_packet) != size+1:
            self.parent.logprint("Unexpected packet size")
            if self.parent.verbose:
                self.parent.logprint(f"Exp {size}, got {len(rest_of_packet)}")
            #print(packet)
            #print(rest_of_packet)
            return b""
        # combine the return code and data and return
        # ignoring header, length, sum in printout
        buf = packet[4:]
        # bugfix specifically for the diag response
        buf += rest_of_packet[:-2] if buf[0] != 0xF1 else rest_of_packet[:-1]
        if self.parent.verbose:
            # Ignore clock responses unless logging them
            if buf[0] != 0xDF or self.parent.clock_logging:
                # Ignore data responses unless logging them
                if buf[0] != 0xEA or self.parent.data_logging:
                    self.parent.logprint(f"Received: {' '.join(f'{b:02X}' for b in buf)}")
        #return bytes([packet[4]])+rest_of_packet[:size-1]
        return buf
