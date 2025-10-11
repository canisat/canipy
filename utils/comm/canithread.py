import time
import threading

class CaniThread:
    """
    Threaded instance reading the port for responses from the radio.

    Attributes:
        parent (CaniPy): A main CaniPy instance that this script will support.
        thread_signal (threading.Event): Prompts the threaded function to halt.
        com_thread (threading.Thread): The actual thread entity looking for responeses.
    """
    def __init__(self, parent:"CaniPy"):
        self.parent = parent
        self.thread_signal = threading.Event()
        self.com_thread = None

    def start(self):
        """
        Starts the thread
        """
        if self.com_thread and self.com_thread.is_alive():
            if self.parent.verbose: print("CaniThread already running")
            return
        self.thread_signal.clear()
        self.com_thread = threading.Thread(target=self.thread_read,name="CaniThread",daemon=True)
        # start com port read thread
        self.com_thread.start()
        if self.parent.verbose: print("CaniThread started")

    def stop(self):
        # Stop thread upon window exit
        self.thread_signal.set()
        if not self.com_thread:
            if self.parent.verbose: print("CaniThread already stopped")
            return
        self.com_thread.join()
        self.com_thread = None
        if self.parent.verbose: print("CaniThread stopped")

    def thread_read(self):
        """
        Main threaded instance, reading serial buffer and handing it over to RX.
        """
        # Keep calling the read method for the port
        while not self.thread_signal.is_set():
            buf = self.thread_buffer()
            if not buf: continue  # sure wish i was buff..
            self.parent.rx.conductor(buf)

    def thread_buffer(self) -> bytes:
        """
        Reads from the serial connection, extracting payloads returned from the radio.

        Example:
            The current serial connection is read for any new commands.

        Returns:
            bytes: Returns the payload that was read.
        """
        if self.parent.serial_conn is None or not self.parent.serial_conn.is_open:
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
            print("Unexpected header size")
            if self.parent.verbose:
                print(f"Exp 5, got {len(packet)}")
            #print(packet)
            return b""
        # verify it is the header
        if packet[:2] != self.parent.header:
            print("Header not found")
            if self.parent.verbose:
                print(packet[:2])
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
            print("Unexpected packet size")
            if self.parent.verbose:
                print(f"Exp {size}, got {len(rest_of_packet)}")
            #print(packet)
            #print(rest_of_packet)
            return b""
        # combine the return code and data and return
        # ignoring header, length, sum in printout
        buf = packet[4:]+rest_of_packet[:-2]
        if self.parent.verbose:
            print(f"Received: {' '.join(f'{b:02X}' for b in buf)}")
        #return bytes([packet[4]])+rest_of_packet[:size-1]
        return buf
