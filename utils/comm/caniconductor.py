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
                self.parent.rx.parse_startup(payload)
            case 0x81:
                self.parent.infoprint("Radio is now powered off.\nGoodnight!")
            case 0x8b:
                if self.parent.verbose:
                    print(
                        f"Line level set to "
                        f"{-payload[3] if payload[3] <= 0x60 else payload[3] - 0x60}dB"
                    )
            case 0x90:
                if self.parent.verbose:
                    print(f"SID {payload[3]}, Ch. {payload[4]}")
                    if payload[5]:
                        # When first tuning to a data channel, like
                        # main WX SID 240, this will still be 0. But tune
                        # normally to another channel after, this becomes 1.
                        # Might be to indicate auxiliary tuning is enabled
                        # to allow simultaneous audio and data tuning.
                        print(f"Data aux is on")
                if (payload[1], payload[2]) not in [(0x01, 0x00), (0x04, 0x0E)]:
                    # Report status if alert, or not ch0
                    self.parent.warnprint(self.parent.rx.fetch_status(payload))
                    return
                self.parent.ch_sid = payload[3]
                self.parent.ch_num = payload[4]
                self.parent.tx.channel_info(payload[4])
            case 0x91:
                # Hacky way to distinguish, but if it's data, it's usually SID
                # Or maybe 11/91 is exclusively sid, im not sure...
                if payload[4]:
                    self.parent.ch_sid = payload[3]
                else:
                    self.parent.ch_num = payload[3]
                if self.parent.verbose:
                    print("Current channel tune cancelled! You will be tuned out!")
                    if payload[3]:
                        print(f"Ready for channel {payload[3]}{' (Data)' if payload[4] else ''}")
                    print("Change channel to resume content")
            case 0x93:
                if self.parent.verbose:
                    print(f"Mute: { {0x00:'Off',0x01:'On'}.get(payload[3],f'?({payload[3]})') }")
            case 0xA2:
                self.parent.rx.parse_extinfo(payload)
            case 0xA5:
                self.parent.rx.parse_chan(payload)
            case 0xB1:
                if len(payload) != 12:
                    if self.parent.verbose:
                        print("Invalid Radio ID length")
                        print(f"Exp 12, got {len(payload)}")
                    return
                # if good, print characters
                self.parent.radio_id = payload[4:12].decode('utf-8')
                self.parent.infoprint(
                    f"Radio ID:\n{payload[4:12].decode('utf-8')}"
                )
            case 0xC1 | 0xC3:
                self.parent.rx.parse_sig(payload)
            case 0xC2:
                if self.parent.verbose:
                    print("Signal strength monitoring status updated")
            case 0xCA:
                # 'A' cmds are WX specific!
                if payload[1] == 0x40:
                    if self.parent.verbose:
                        if payload[2] == 0xff:
                            print(f"WX - Error setting up data RX on {payload[4]}")
                            if payload[3] == 0x08:
                                # Not exactly sure if this correct...
                                print("Unable to listen as data")
                            if payload[3] == 0x0a:
                                print("Data track not available for current subscription")
                            return
                        if payload[4] != 0xff:
                            print(f"WX - Ready for data from {payload[4]}")
                        else:
                            print("WX - Data stopped")
                    return
                if payload[1] == 0x43:
                    self.parent.infoprint("WX ping received")
                    return
                if payload[1] == 0x64:
                    self.parent.infoprint(
                        f"WX version:\n"
                        f"{payload[2:].decode('utf-8').rstrip(chr(0))}"
                    )
            case 0xCF | 0xD0:
                # Usually 50/D0, but 4F/CF may also be used to
                # achieve the same thing, especially with
                # receivers that are also tuned to data!
                if payload[3]:
                    self.parent.infoprint(f"Monitoring channel {payload[3]}")
                    return
                self.parent.infoprint("Channel monitoring stopped")
            case 0xD1:
                if payload[2] == 0x01:
                    # Store only if channel numbers match!
                    if payload[1] == self.parent.ch_num:
                        self.parent.ch_name = payload[3:19].decode('utf-8')
                    if self.parent.verbose:
                        print("===Channel Name===")
                        print(f"Channel {payload[1]}")
                        print(payload[3:19].decode('utf-8'))
                        # Trailing bytes, this could be length side effect?
                        # Like with whats happening with extended info?
                        # Treat as debug info for now.
                        #if self.parent.verbose:
                        print(' '.join(f'{b:02X}' for b in payload[19:]))
                        print("==================")
            case 0xD2:
                if payload[3] == 0x01:
                    if payload[1] == self.parent.ch_num:
                        self.parent.cat_id = payload[2]
                        self.parent.cat_name = payload[4:].decode('utf-8')
                    if self.parent.verbose:
                        print("===Ch. Category===")
                        print(f"Channel {payload[1]}")
                        print(payload[4:].decode('utf-8'))
                        #if self.parent.verbose:
                        print(f"Cat ID: {payload[2]:02X}")
                        print("==================")
            case 0xD3:
                if payload[2] == 0x01:
                    if payload[1] == self.parent.ch_num:
                        self.parent.artist_name = payload[3:19].decode('utf-8')
                        self.parent.title_name = payload[19:].decode('utf-8')
                    if self.parent.verbose:
                        print("===Program Info===")
                        print(f"Channel {payload[1]}")
                        print(payload[3:19].decode('utf-8'))
                        print(payload[19:].decode('utf-8'))
                        print("==================")
            case 0xD4:
                if payload[2] == 0x01:
                    if payload[1] == self.parent.ch_num:
                        self.parent.artist_name = payload[3:].decode('utf-8').rstrip(chr(0))
                    if self.parent.verbose:
                        print("===Artist Info.===")
                        print(f"Channel {payload[1]}")
                        print(payload[3:].decode('utf-8').rstrip(chr(0)))
                        print("==================")
            case 0xD5:
                if payload[2] == 0x01:
                    if payload[1] == self.parent.ch_num:
                        self.parent.title_name = payload[3:].decode('utf-8').rstrip(chr(0))
                    if self.parent.verbose:
                        print("===Title  Info.===")
                        print(f"Channel {payload[1]}")
                        print(payload[3:].decode('utf-8').rstrip(chr(0)))
                        print("==================")
            case 0xD6:
                if payload[3] == 0x01 or payload[4] == 0x01:
                    # TODO: Will figure out how to store this info later...
                    if self.parent.verbose:
                        print("===Program Len.===")
                        print(f"Channel {payload[1]}")
                        #if self.parent.verbose:
                        print(f"Time Format: {payload[2]:02X}")
                        if payload[3] == 0x01:
                            print(f"Started {round(((payload[5] << 8) | payload[6])/60)}m ago")
                        if payload[4] == 0x01:
                            print(f"Ends in {round(((payload[7] << 8) | payload[8])/60)}m")
                        print("==================")
            case 0xDE:
                if self.parent.verbose:
                    print("Clock monitoring status updated")
            case 0xDF:
                self.parent.rx.parse_clock(payload)
            case 0xE0:
                self.parent.infoprint("Fetched activation info")
            case 0xE1:
                self.parent.warnprint("Fetched deactivation info")
            case 0xE3:
                self.parent.rx.parse_firminf(payload)
            case 0xE4 | 0xF4:
                # Acknowledgement of Direct responses.
                # nsayer ref listens to E4 though?? differs by 4th opcode
                # TODO: cover both until better understood
                if self.parent.verbose:
                    print(f"Direct command Acknowledged ({payload[0]:02X})")
            case 0xEA:
                if payload[1] == 0xD0:
                    # Write data frames
                    self.parent.wx.parse_data(payload, True)
                    return
                # Ignore if unsupported packet (not D0)
                if self.parent.verbose: print("Data packet received")
            case 0xF0:
                if self.parent.verbose:
                    print("Diagnostic info monitoring status updated")
            case 0xF1:
                if self.parent.verbose:
                    # TODO: examine how diag is laid out, appears to be 8 or 9 fields
                    print("=== DIAGNOSTIC ===")
                    print(payload[2:].decode('utf-8'))
                    print("==================")
            case 0xF2:
                # Direct idle frames.
                # Counted, but generally just ignored.
                self.parent.direct_idleframes += 1
            case 0xFF:
                errstr = "Warning! Radio reported an error"
                if (payload[1], payload[2]) == (0x01, 0x00):
                    # 01 00 (aka OK) on error, typically corresponds to antenna
                    errstr += "\nAntenna not detected, check antenna"
                elif (payload[1], payload[2]) == (0xFF, 0xFF):
                    # If it's all F's, it's something serious!!!
                    # (Likely has a message, print it out!)
                    errstr += f"\n{payload[3:].decode('utf-8')}"
                else:
                    errstr += self.parent.rx.fetch_status(payload)
                if self.parent.verbose:
                    print(f"{payload[1]:02X} {payload[2]:02X} {payload[3:].decode('utf-8')}")
                errstr += "\nRadio may still be operated"
                errstr += "\nIf errors persist, check or power-cycle the radio"
                self.parent.errorprint(errstr)
            case _:
                if self.parent.verbose:
                    print(f"Unknown return code {hex(payload[0])}")