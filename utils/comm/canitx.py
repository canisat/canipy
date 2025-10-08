class CaniTX:
    """
    Functions related to transmission of commands.

    Attributes:
        parent (CaniPy): A main CaniPy instance that this script will support.

    Lambda:
        mute(): Mutes audio.
        unmute(): Unmutes audio.

        sigmon_enable(): Enable signal monitoring.
        sigmon_disable(): Disable signal monitoring.

        chanmon_disable(): Disable channel monitoring.

        diagmon_enable(): Enable diagnostics info monitoring.
        diagmon_disable(): Disable diagnostics info monitoring.

        curr_channel_info(): Prompts radio to report info for current channel.
        next_channel_info(): Prompts radio to report info for the channel ahead of the current one.
        prev_channel_info(): Prompts radio to report info for the channel behind the current one.

        curr_ext_info(): Prompts radio to report extended program info for current channel.
    """
    # Functions will be moved here gradually
    def __init__(self, parent:"CaniPy"):
        self.parent = parent

        self.mute = lambda: self.set_mute(True)
        self.unmute = lambda: self.set_mute(False)

        self.sigmon_enable = lambda: self.signal_mon(True)
        self.sigmon_disable = lambda: self.signal_mon(False)

        self.chanmon_disable = lambda: self.chan_mon(0)

        self.diagmon_enable = lambda: self.diag_mon(True)
        self.diagmon_disable = lambda: self.diag_mon(False)

        self.curr_channel_info = lambda: self.channel_info(self.ch_num)
        self.next_channel_info = lambda: self.send(bytes([0x25, 0x09, self.ch_num, 0x00]))
        self.prev_channel_info = lambda: self.send(bytes([0x25, 0x0A, self.ch_num, 0x00]))

        self.curr_ext_info = lambda: self.ext_info(self.ch_num)

    def send(self, payload:bytes) -> bytes:
        """
        Prepares and transmits a packet to be sent to the radio.
        Takes a bare payload and encloses it with the necessary header, length, and footer.

        Example:
            A payload of "31" is provided to fetch the radio ID.
            5A A5 & two-byte length of the payload (1 byte) are added as the prefix, then ED ED as the suffix.
            The resulting transmission is "5A A5 00 01 31 ED ED".

        Args:
            payload (bytes): A command, comprised as a set of bytes, to be encased and sent to the radio.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.parent.serial_conn is None or not self.parent.serial_conn.is_open:
            print("No serial port in use")
            return b""
        length = len(payload).to_bytes(2, byteorder='big')
        command = self.header + length + payload + self.tail
        self.parent.serial_conn.write(command)
        if self.parent.verbose:
            print(f"Sent: {' '.join(f'{b:02X}' for b in payload)}")
        return payload

    def power_up(self, ch_lbl:int=16, cat_lbl:int=16, title_lbl:int=36, loss_exp:bool=True) -> bytes:
        """
        Sends in a command to power on the radio tuner.
        Defaults are 16 characters long for channel and category labels, and 36 for title label
        mainly due to a possible oversight with the radio firmware when fetching extended labels.

        Example:
            The radio will be provided with "00 10 10 24 01".
            Power up with 16 char channel and category label size, 36 char title size, expect loss of power.

        Args:
            ch_lbl (int, optional): Maximum channel label character length. Default to 16 (10 hex).
            cat_lbl (int, optional): Maximum category label character length. Default to 16 (10 hex).
            title_lbl (int, optional): Maximum program title label character length. Default to 36 (24 hex).
            loss_exp (bool, optional): Indicate if the tuner is in a board that may shut off without notice. Default to True.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        print("Powering up")
        return self.send(bytes([0x00, ch_lbl, cat_lbl, title_lbl, loss_exp]))

    def power_down(self, pwr_sav:bool=False) -> bytes:
        """
        Sends in a command to power down the radio tuner.

        Example:
            The radio will be provided with "01 00".
            Power off, no power save.

        Args:
            pwr_sav (bool, optional): Set radio to a power saving state instead. Default to False.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        print("Powering down")
        return self.send(bytes([0x01, pwr_sav]))

    def set_linevol(self, db:int) -> bytes:
        """
        Sends in a command to set the audio level/gain of the radio's line output,
        mayyyybe relative to full/digital scale (dBFS)?
        Ideal to keep it at 0 decibels unless needed to be changed.
        Output level can be between -96dB (db=96) to 24dB (db=78).

        Example:
            To set output to -96dB, the radio will be provided with "0B 96".
            Set line level to -96dB.

        Args:
            db (int): The gain value to set on the radio.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        # TODO: Have to check this again to get the correct scale.
        if self.parent.verbose: print(f"Setting gain to {db}dB")
        return self.send(bytes([0x0B, db]))

    def change_channel(self, channel:int, is_sid:bool=False, data:bool=False, prg_type:int=0) -> bytes:
        """
        Sends in a command to the tuner to switch to another channel based on assigned number or ID.
        Some channels (i.e. SID 240/F0) can even be tuned as data.

        Example:
            To tune to audio channel number 1, the radio will be provided with "10 02 01 00 00 01".
            Tunes to channel 1, no data, program type 0, route to audio port (1).

        Args:
            channel (int): The channel value.
            is_sid (bool, optional): Indicate if provided number is a service ID. Default to False.
            data (bool, optional): Indicate to tune channel as a data feed and route data to download terminal. Default to False.
            prg_type (int, optional): Program type. Magic value; all known instances just leave it at 0 so it's defaulted to 0.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if channel not in range(256):
            print("Invalid channel value")
            return b""
        print(f"Changing to {'channel' if not is_sid else 'ID'} {channel}{' (Data)' if data else ''}")
        if not is_sid:
            self.parent.ch_num = channel
        else:
            self.parent.ch_sid = channel
        return self.send(bytes([0x10, 0x02 - is_sid, channel, data, prg_type, 0x01 + data]))

    def channel_cancel(self, channel:int=0, data:bool=False) -> bytes:
        """
        Sends in a command to the tuner to stop listening to the current channel, like picking up the needle off a record.
        The command then supplies a channel for the radio to "pre-load" and quickly tune after client processing.
        Additional byte is to indicate if the channel is for "pre-loading" in data mode.
        Running this will tune out of the current channel. User must tune once again to resume content.
        Channel number could just be the assigned number or service ID? No idea...
        This is mainly used for data channels to stop/finish data download before the channel loops the data.
        This command was not community documented, but is utilized by official implementations.

        Example:
            To stop listening and prepare the radio for channel 1, the radio will be provided with "11 01 00".
            Stop and prepare for channel 1, no data.

        Args:
            channel (int, optional): The channel value to preload. Default to 0 as in don't preload. Hopefully that'll work fine...
            data (bool, optional): Indicate to treat the preloaded channel as a data feed. Default to False.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if channel not in range(256):
            print("Invalid channel value")
            return b""
        if self.parent.verbose: print(f"Cancelling and preparing for channel {channel}")
        return self.send(bytes([0x11, channel, data]))

    def set_mute(self, mute:bool) -> bytes:
        """
        Sends in a command to the tuner to mute or unmute the audio.

        Example:
            To mute audio, the radio will be provided with "13 01".
            Mute the audio.

        Args:
            mute (bool): Prompt to mute or unmute audio.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        print(f"{'' if mute else 'Un-'}Muting Audio")
        return self.send(bytes([0x13, mute]))

    def ext_info(self, channel:int) -> bytes:
        """
        Sends in a command to the tuner to report program information at full char length.
        This is known as "extended" channel info.

        Example:
            To check the ext status of channel number 1, the radio will be provided with "22 01".
            Report ext program status for channel 1.

        Args:
            channel (int): The channel value.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if channel not in range(256):
            print("Invalid channel value")
            return b""
        if self.parent.verbose: print(f"Check RX for extinfo on {channel}")
        # I set title size to 0x24 earlier to see if this fixes out the botched output.
        return self.send(bytes([0x22, channel]))

    def channel_info(self, channel:int, is_sid:bool=False, prg_type:int=0) -> bytes:
        """
        Sends in a command to the tuner to report the channel's program information provided an assigned number or ID.

        Example:
            To check the info of channel number 1, the radio will be provided with "25 08 01 00".
            Report info for channel 1, program type 0.

        Args:
            channel (int): The channel value.
            is_sid (bool, optional): Indicate if provided number is a service ID. Default to False.
            prg_type (int, optional): Program type. Magic value; all known instances just leave it at 0 so it's defaulted to 0.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if channel not in range(256):
            print("Invalid channel value")
            return b""
        if self.parent.verbose: print(f"Check RX for info on {channel}")
        # 07 allows for checking by SID
        return self.send(bytes([0x25, 0x08 - is_sid, channel, prg_type]))

    def get_radioid(self) -> bytes:
        """
        Sends in a command to the tuner to report its radio ID.
        Supported radio IDs are 8-char alphanumeric (Excluding letters I, O, S, F).

        Example:
            The radio will be provided with "31".

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.parent.verbose: print("Check RX for ID")
        return self.send(bytes([0x31]))

    def signal_mon(self, toggle:bool) -> bytes:
        """
        Sends in a command to the tuner to monitor and periodically report signal strength.
        Responses are the same as what you get after sending in 43 hex, but without first two status bytes and C/N info.
        This was not a community-documented command.

        Example:
            To enable signal monitoring, the radio will be provided with "42 01".
            Turn on signal monitoring.

        Args:
            toggle (bool): Prompt to enable or disable monitoring.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.parent.verbose: print(f"Asking radio to {'' if toggle else 'not '}monitor signal status")
        return self.send(bytes([0x42, toggle]))

    def signal_info(self) -> bytes:
        """
        Sends in a command to the tuner to report "extended" signal quality info.

        Example:
            The radio will be provided with "43".

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.parent.verbose: print("Check RX for signal info")
        # It's known that 42 is monitor, but these two are
        # the only ones documented. idk if theres a 41 or 40...
        return self.send(bytes([0x43]))

    def clock_mon(self, toggle:bool) -> bytes:
        """
        Prompts the radio to report the time as synced with the service.

        Example:
            If "toggle" is True, the radio will be provided with
            "4E 01" to enable the clock.

        Args:
            toggle (bool): Prompt to enable or disable time reports.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.parent.verbose: print(f"Turning {'on' if toggle else 'off'} the clock")
        return self.send(bytes([0x4E, toggle]))

    def chan_mon(self, channel:int, is_data_on:bool=False, serv_mon:bool=True, prgtype_mon:bool=True, inf_mon:bool=True, ext_mon:bool=True) -> bytes:
        """
        Sends in a command to the tuner to monitor and periodically report information for the given channel number.

        Example:
            To monitor all channel 1 info, the radio will be provided with "50 01 01 01 01 01".
            Turn on monitoring for channel 1, monitor service ID, prog type, info, and extended.

        Args:
            channel (int): The channel value.
            is_data_on (bool, optional): Ensure this gets set to True if using the data RX. Default is false.
            serv_mon (bool, optional): Monitor changes to the channel's service ID. Default is true.
            prgtype_mon (bool, optional): Monitor changes to the channel's program type. Default is true.
            inf_mon (bool, optional): Monitor changes in the program info for the channel. Default is true.
            ext_mon (bool, optional): Monitor changes in the extended program info for the channel. Default is true.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if channel not in range(256):
            print("Invalid channel value")
            return b""
        if not channel:
            # If channel is 0, assume it's to not listen to anything.
            serv_mon = False
            prgtype_mon = False
            inf_mon = False
            ext_mon = False
        if self.parent.verbose: print(f"Asking radio to monitor channel {channel}")
        return self.send(bytes([0x50 - is_data_on, channel, serv_mon, prgtype_mon, inf_mon, ext_mon]))

    def diag_mon(self, toggle:bool) -> bytes:
        """
        Sends in a command to the tuner to what looks like some diagnostics information.
        Will have to check again later what the responses mean.
        This was not a community-documented command.

        Example:
            To enable diagnostics monitoring, the radio will be provided with "60 01".
            Turn on diagnostics monitoring.

        Args:
            toggle (bool): Prompt to enable or disable monitoring.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.parent.verbose: print(f"Asking radio to {'' if toggle else 'not '}monitor extra info")
        # F0 returned when command is acknowledged.
        # Messages will be received periodically as F1, followed by the info.
        # Would 63 designate to return this info ad-hoc? Who knows!
        return self.send(bytes([0x60, toggle]))

    def firm_ver(self, magic:int=5) -> bytes:
        """
        Sends in a command to the tuner to report its firmware version info and build dates.
        By default, SDEC, CMB, and RX versions are reported.

        Example:
            The radio will be provided with "70 05".

        Args:
            magic (int, optional): Magic value; all known instances just leave it at 5. Default to 5.

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        if self.parent.verbose: print("Check RX for radio firmware version")
        return self.send(bytes([0x70, magic]))

    def crash_override(self) -> bytes:
        """
        Manually enter payload for debugging purposes.
        Hack the planet!

        Returns:
            bytes: Echoes back the payload it's been given for debugging purposes.
        """
        # FOR DEBUG USE
        print("Careful now!")
        print("You're sending commands directly!")
        return self.send(
            bytes.fromhex(
                input("Enter payload: ").strip().lower().replace("0x", "").replace(" ", "")
            )
        )
