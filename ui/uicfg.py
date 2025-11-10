import configparser, os

class InterfaceCfg:
    def __init__(self, parent):
        self.parent = parent

        self.defaults = {
            "clock": {
                "tz": "Eastern",
                "dst": "False",
                "miltime": "False"
            },
            "preset": {
                "1": "0",
                "2": "0",
                "3": "0",
                "4": "0",
                "5": "0",
                "6": "0"
            }
        }

        self.savemapper = {
            "clock": {
                "tz": self.parent.tzGuiVar,
                "dst": self.parent.dstToggle,
                "miltime": self.parent.milclockToggle
            },
            "preset": {
                "1": self.parent.chPresets[0],
                "2": self.parent.chPresets[1],
                "3": self.parent.chPresets[2],
                "4": self.parent.chPresets[3],
                "5": self.parent.chPresets[4],
                "6": self.parent.chPresets[5]
            }
        }

        self.validity = {
            "clock": {
                "tz": self.parent.timezoneOptions,
                "dst": ("True", "False"),
                "miltime": ("True", "False")
            },
            "preset": {
                "1": range(0, 256),
                "2": range(0, 256),
                "3": range(0, 256),
                "4": range(0, 256),
                "5": range(0, 256),
                "6": range(0, 256)
            }
        }

        self.settings = configparser.ConfigParser()

        self.cfgfile = "canipy.ini"

        self.load_file()
    
    def update_tz(self, name:str):
        self.parent.tzGuiVar.set(name)
        self.save_file()

    def set_preset(self, preset:int, ch:int):
        # set if greater than 0
        if ch > 0:
            self.parent.chPresets[preset].set(ch)
            self.settings["preset"][str(preset+1)] = str(ch)
            self.save_file()
            self.parent.infobox(f"Preset {preset+1} set to channel {ch}")

    def clear_preset(self, preset:int):
        self.parent.chPresets[preset].set(0)
        self.settings["preset"][str(preset+1)] = "0"
        self.save_file()
        self.parent.infobox(f"Preset {preset+1} cleared")
    
    def clear_all_presets(self):
        for i in range(len(self.parent.chPresets)):
            self.parent.chPresets[i].set(0)
        self.settings["preset"] = self.defaults["preset"]
        self.save_file()
        self.parent.infobox(f"All presets cleared")

    def load_defaults(self, section:str):
        self.settings[section] = self.defaults[section]

    def load_all_defaults(self):
        # defaults to load
        for section in self.defaults.keys():
            self.load_defaults(section)
    
    def check_settings(self, section:str):
        # Check if section exists
        if not self.settings.has_section(section):
            # Load defaults if not present
            self.load_defaults(section)
            return
        # Check validity of options
        for option in self.defaults[section]:
            fileval = self.settings[section].get(option, self.defaults[section][option])
            if fileval not in map(str,self.validity[section][option]):
                fileval = self.defaults[section][option]
            self.settings[section][option] = fileval

    def check_all_settings(self):
        for section in self.defaults.keys():
            self.check_settings(section)

    def load_file(self):
        try:
            # Throw exception if does not exist or empty
            if not os.path.exists(self.cfgfile) or os.path.getsize(self.cfgfile) == 0:
                raise FileNotFoundError
            # Load settings
            self.settings.read(self.cfgfile)
        except (FileNotFoundError, configparser.Error):
            # Load defaults if exception thrown
            self.load_all_defaults()
            return
        # Verify the structure
        self.check_all_settings()

    def save_file(self):
        for section in self.savemapper:
            for option in self.savemapper[section]:
                self.settings[section][option] = str(self.savemapper[section][option].get())
        with open(self.cfgfile, "w") as file:
            self.settings.write(file)
