import time

class CaniDX:
    """
    Functions related to Direct receiver commands.

    Attributes:
        parent (CaniPy): A main CaniPy instance that this script will support.
    """
    # Functions will be moved here gradually
    def __init__(self, parent:"CaniPy"):
        self.parent = parent

    def enable(self):
        """
        A series of necessary Direct commands to allow for compatible operation.
        This sets the Direct to enable listening mode, voltage, and unmutes the DAC.
        Think of it as a second power switch, as Direct receivers are usually
        installed in vehicles. The Direct waits for the client headunit to start up
        first, which then send these series of commands.
        """
        # There's also hint at 74 0D,
        # no idea what 0D does at the moment.
        # Java ref only used it as a suffix placeholder.
        # Assuming this sequence works regardless.

        self.com_listen(True)
        time.sleep(1)  # These sleeps should be event driven instead

        self.voltage(True, True)
        time.sleep(1)

        # RX might not be received when unmuting,
        # Let the function finish as-is after this
        self.dac_mute(False)

    def com_listen(self, toggle:bool) -> bytes:
        """
        Sets the Direct's serial module to allow incoming commands
        to the tuner daughterboard.

        Example:
            The radio will be provided with "74 00 01".
            Start listening to serial commands for this session.

        Args:
            toggle (bool): Prompt to enable or disable listening mode.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        #if self.parent.verbose:
        print("Direct listening mode")
        return self.parent.tx.send(bytes([0x74, 0x00, toggle]))

    def voltage(self, toggle1:bool, toggle2:bool) -> bytes:
        """
        Instructs the serial module to power up the hardware inside the Direct.
        There are two flags, not sure what each are for. Maybe tuner and DAC
        daughterboards each? Assume both are needed for now, but might
        investigate and separate down the road.

        Example:
            The radio will be provided with "74 02 01 01".
            Power up the hardware inside the Direct.

        Args:
            toggle1 (bool): Magic flag. Documentation passes True. Either tuner or DAC?
            toggle2 (bool): Magic flag. Documentation passes True. Either tuner or DAC?

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        # TODO: Figure out what each flag corresponds to!
        #if self.parent.verbose:
        print("Direct voltage on")
        return self.parent.tx.send(bytes([0x74, 0x02, toggle1, toggle2]))

    def dac_mute(self, mute:bool) -> bytes:
        """
        Sends in a command to the Direct to mute or unmute the DAC daughterboard.
        This is different from the native audio output of a PCR or WX.
        A response might not be received after sending this command!

        Example:
            To unmute the DAC, the radio will be provided with "74 0B 00".
            Unmute the DAC.

        Args:
            mute (bool): Prompt to mute or unmute DAC.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        #if self.parent.verbose:
        print(f"{'' if mute else 'Un-'}Muting Direct DAC")
        return self.parent.tx.send(bytes([0x74, 0x0B, mute]))
