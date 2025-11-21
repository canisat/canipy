class CaniConductor:
    """
    Relays received responses to corresponding functions.

    Attributes:
        parent (CaniPy): A main CaniPy instance that this script will support.
    """
    def __init__(self, parent:"CaniPy"):
        self.parent = parent

    def go(self, payload:bytes):
        """
        Takes in a response payload to then coordinate the information stored within.
        The message type is checked to select how to handle it.

        Args:
            payload (bytes): A response, comprised as a set of bytes, to parse the information from.
        """
        # payload[1] and payload[2] appear to
        # always be status code and detail respectively,
        # except if it's an event driven response.
        match payload[0]:
            case 0x80:
                self.parent.infoprint("Radio started")
                self.parent.rx.parse_startup(payload)
                # Autostart clock and signal monitoring if GUI
                if self.parent.gui:
                    self.parent.tx.clock_mon(True)
                    self.parent.tx.signal_mon(True)
            case 0x81:
                # Reset display values to defaults!
                self.parent.reset_display()
                if (payload[1], payload[2]) != (0x01, 0x00):
                    # Report status if alert
                    self.parent.warnprint(self.parent.rx.fetch_status(payload))
                # Prompt shut off
                self.parent.infoprint("Radio is now powered off\nGoodnight!")
            case 0x8b:
                self.parent.logprint(
                    f"Line level set to "
                    f"{-payload[3] if payload[3] <= 0x60 else payload[3] - 0x60}dB"
                )
            case 0x90:
                self.parent.logprint(f"SID {payload[3]}, Ch. {payload[4]}")
                if payload[5]:
                    # When first tuning to a data channel, like
                    # main WX SID 240, this will still be 0. But tune
                    # normally to another channel after, this becomes 1.
                    # Might be to indicate auxiliary tuning is enabled
                    # to allow simultaneous audio and data tuning.
                    self.parent.logprint(f"Data aux is on")
                    # Data is on in this case
                    self.parent.data_in_use = True
                if (payload[1], payload[2]) == (0x04, 0x0E):
                    # Channel 0 is for reporting ID.
                    # just return radio ID.
                    self.parent.tx.get_radioid()
                    return
                if (payload[1], payload[2]) != (0x01, 0x00):
                    # Report status if alert
                    self.parent.warnprint(self.parent.rx.fetch_status(payload))
                    return
                # Set as current ch
                self.parent.ch_sid = payload[3]
                self.parent.ch_num = payload[4]
                # Clear display values
                self.parent.ch_name = ""
                self.parent.artist_name = ""
                self.parent.title_name = ""
                self.parent.cat_name = ""
                self.parent.cat_id = 0
                # Fetch channel info
                self.parent.tx.channel_info(payload[4])
                self.parent.tx.ext_info(payload[4])
                # If using a GUI subsystem, also monitor channel.
                if self.parent.gui:
                    self.parent.tx.chan_mon(payload[4])
            case 0x91:
                # Hacky way to distinguish, but if it's data, it's usually SID
                # Or maybe 11/91 is exclusively sid, im not sure...
                if payload[4]:
                    self.parent.ch_sid = payload[3]
                else:
                    self.parent.ch_num = payload[3]
                self.parent.logprint("Current channel tune cancelled! You will be tuned out!")
                if payload[3]:
                    self.parent.logprint(f"Ready for channel {payload[3]}{' (Data)' if payload[4] else ''}")
                self.parent.logprint("Change channel to resume content")
            case 0x93:
                self.parent.logprint(f"Mute: { {0x00:'Off',0x01:'On'}.get(payload[3],f'?({payload[3]})') }")
            case 0xA2:
                self.parent.rx.parse_extinfo(payload)
            case 0xA5:
                if (payload[1], payload[2]) == (0x02, 0x04):
                    # If trying to fetch A5 on a data ch,
                    # it's usually a callback from 90.
                    # Report to user that data is starting.
                    self.parent.infoprint("Data download started")
                    return
                if (payload[1], payload[2]) == (0x04, 0x0E):
                    # Channel 0 is for reporting ID.
                    # just return radio ID.
                    self.parent.tx.get_radioid()
                    return
                self.parent.rx.parse_chan(payload)
            case 0xB1:
                if len(payload) != 12:
                    self.parent.logprint("Invalid Radio ID length")
                    if self.parent.verbose:
                        self.parent.logprint(f"Exp 12, got {len(payload)}")
                    return
                # if good, print characters
                self.parent.radio_id = payload[4:12].decode("latin-1")
                self.parent.infoprint(
                    f"Radio ID\n\n{payload[4:12].decode('latin-1')}"
                )
            case 0xC1 | 0xC3:
                self.parent.rx.parse_sig(payload)
            case 0xC2:
                self.parent.logprint("Signal strength monitoring status updated")
            case 0xCA:
                # "A" cmds are WX specific!
                if payload[1] == 0x40:
                    if payload[2] == 0xff:
                        self.parent.logprint(f"Error setting up data RX on {payload[4]}")
                        if payload[3] == 0x08:
                            # Not exactly sure if this correct...
                            self.parent.logprint("Unable to listen as data")
                        if payload[3] == 0x0a:
                            self.parent.logprint("Data track not available for current subscription")
                        return
                    if payload[4] == 0xff:
                        self.parent.infoprint("Data download stopped")
                        return
                    self.parent.logprint(f"Ready for data from {payload[4]}")
                    return
                if payload[1] == 0x43:
                    self.parent.infoprint("WX ping received")
                    return
                if payload[1] == 0x64:
                    self.parent.infoprint(
                        f"WX Version\n\n"
                        f"{payload[2:].decode('latin-1').rstrip(chr(0))}"
                    )
            case 0xCF | 0xD0:
                # Usually 50/D0, but 4F/CF may also be used to
                # achieve the same thing, especially with
                # receivers that are also tuned to data!
                if payload[3]:
                    self.parent.logprint(f"Monitoring channel {payload[3]}")
                    return
                self.parent.logprint("Channel monitoring stopped")
            case 0xD1:
                if payload[2] == 0x01:
                    # Store only if channel numbers match!
                    if payload[1] == self.parent.ch_num:
                        self.parent.ch_name = payload[3:19].decode("latin-1").strip()
                    self.parent.logprint("===Channel Name===")
                    self.parent.logprint(f"Channel {payload[1]}")
                    self.parent.logprint(payload[3:19].decode("latin-1"))
                    # Trailing bytes, this could be length side effect?
                    # Like with whats happening with extended info?
                    # Treat as debug info for now.
                    if self.parent.verbose:
                        self.parent.logprint(" ".join(f'{b:02X}' for b in payload[19:]))
                    self.parent.logprint("==================")
            case 0xD2:
                if payload[3] == 0x01:
                    if payload[1] == self.parent.ch_num:
                        self.parent.cat_id = payload[2]
                        self.parent.cat_name = payload[4:].decode("latin-1").strip()
                    self.parent.logprint("===Ch. Category===")
                    self.parent.logprint(f"Channel {payload[1]}")
                    self.parent.logprint(payload[4:].decode("latin-1"))
                    if self.parent.verbose:
                        self.parent.logprint(f"Cat ID: {payload[2]:02X}")
                    self.parent.logprint("==================")
            case 0xD3:
                if payload[2] == 0x01:
                    if payload[1] == self.parent.ch_num:
                        self.parent.artist_name = payload[3:19].decode("latin-1").strip()
                        self.parent.title_name = payload[19:].decode("latin-1").strip()
                    self.parent.logprint("===Program Info===")
                    self.parent.logprint(f"Channel {payload[1]}")
                    self.parent.logprint(payload[3:19].decode("latin-1"))
                    self.parent.logprint(payload[19:].decode("latin-1"))
                    self.parent.logprint("==================")
            case 0xD4:
                if payload[2] == 0x01:
                    # if payload[1] == self.parent.ch_num:
                    #     self.parent.artist_name = payload[3:].decode("latin-1").rstrip(chr(0)).strip()
                    # self.parent.logprint("===Artist Info.===")
                    # self.parent.logprint(f"Channel {payload[1]}")
                    # self.parent.logprint(payload[3:].decode("latin-1").rstrip(chr(0)))
                    # self.parent.logprint("==================")
                    # Extinfo monitoring is weird as hell...
                    # Just fetch manually instead
                    self.parent.tx.ext_info(payload[1])
            case 0xD5:
                if payload[2] == 0x01:
                    # if payload[1] == self.parent.ch_num:
                    #     self.parent.title_name = payload[3:].decode("latin-1").rstrip(chr(0)).strip()
                    # self.parent.logprint("===Title  Info.===")
                    # self.parent.logprint(f"Channel {payload[1]}")
                    # self.parent.logprint(payload[3:].decode("latin-1").rstrip(chr(0)))
                    # self.parent.logprint("==================")
                    # Extinfo monitoring is weird as hell...
                    # Just fetch manually instead
                    self.parent.tx.ext_info(payload[1])
            case 0xD6:
                if payload[3] == 0x01 or payload[4] == 0x01:
                    self.parent.logprint("===Program Len.===")
                    self.parent.logprint(f"Channel {payload[1]}")
                    if self.parent.verbose:
                        self.parent.logprint(f"Time Format: {payload[2]:02X}")
                    if payload[3] == 0x01:
                        self.parent.logprint(f"Started {round(((payload[5] << 8) | payload[6])/60)}m ago")
                    if payload[4] == 0x01:
                        self.parent.logprint(f"Ends in {round(((payload[7] << 8) | payload[8])/60)}m")
                    self.parent.logprint("==================")
            case 0xDE:
                self.parent.logprint("Clock monitoring status updated")
            case 0xDF:
                self.parent.rx.parse_clock(payload, self.parent.clock_logging)
            case 0xE0:
                self.parent.infoprint("Fetched activation info")
            case 0xE1:
                self.parent.warnprint("Fetched deactivation info")
            case 0xE2:
                self.parent.warnprint(
                    f"An error occurred when fetching activation info\n"
                    f"Please restart radio or contact the service provider to refresh"
                )
            case 0xE3:
                self.parent.rx.parse_firminf(payload)
            case 0xE4 | 0xF4:
                # Acknowledgement of Direct responses.
                # nsayer ref listens to E4 though?? differs by 4th opcode
                # TODO: cover both until better understood
                self.parent.logprint(f"Direct command Acknowledged ({payload[0]:02X})")
            case 0xEA:
                if payload[1] == 0xD0:
                    # Write data frames
                    self.parent.wx.parse_data(payload, True, self.parent.data_logging)
                    return
                # Ignore if unsupported packet (not D0)
                self.parent.logprint("Data packet received")
            case 0xF0:
                self.parent.logprint("Diagnostic info monitoring status updated")
            case 0xF1:
                if self.parent.verbose:
                    # Print out diag info, 9 fields
                    self.parent.logprint("=== DIAGNOSTIC ===")
                    diaginf = payload[1:].decode("latin-1")
                    fields = [diaginf[i:i+8] for i in range(0, len(diaginf), 8)]
                    for field in fields:
                        self.parent.logprint(f"{field[0]}. {field[1:]}")
                    self.parent.logprint("==================")
            case 0xF2:
                # Direct idle frames.
                # Counted, but generally just ignored.
                self.parent.direct_idleframes += 1
            case 0xFF:
                errstr = ""
                if (payload[1], payload[2]) == (0x01, 0x00):
                    # 01 00 (aka OK) on error, typically corresponds to antenna
                    errstr += "Antenna not detected, check antenna"
                elif (payload[1], payload[2]) == (0xFF, 0xFF):
                    # If it's all F's, it's something serious!!!
                    # (Likely has a message, print it out!)
                    errstr += payload[3:].decode("latin-1")
                else:
                    errstr += self.parent.rx.fetch_status(payload)
                if self.parent.verbose:
                    errstr += f"\n{payload[1]:02X} {payload[2]:02X} {payload[3:].decode('latin-1')}"
                self.parent.errorprint(errstr)
            case _:
                self.parent.logprint(f"Unknown return code {hex(payload[0])}")
                # Best to print out the whole thing if not known, likely undocumented!
                self.parent.logprint(f"Received: {' '.join(f'{b:02X}' for b in payload)}")