import configparser, os

class InterfaceCfg:
    def __init__(self, parent):
        self.parent = parent

        self.defaults = {
            "clock": {
                "tz": "Eastern",
                "dst": "False",
                "miltime": "False"
            }
        }

        self.savemapper = {
            "clock": {
                "tz": self.parent.tzGuiVar,
                "dst": self.parent.dstToggle,
                "miltime": self.parent.milclockToggle
            }
        }

        self.validity = {
            "clock": {
                "tz": self.parent.timezoneOptions,
                "dst": ("True", "False"),
                "miltime": ("True", "False")
            }
        }

        self.settings = configparser.ConfigParser()

        self.cfgfile = "canipy.ini"

        self.load_file()
    
    def update_tz(self, name:str):
        self.parent.tzGuiVar.set(name)
        self.save_file()
    
    def load_clock_defaults(self):
        self.settings["clock"] = self.defaults["clock"]

    def load_all_defaults(self):
        # defaults to load
        self.load_clock_defaults()

        # write config
        self.save_file()
    
    def check_clock_settings(self):
        # Check if section exists
        if not self.settings.has_section("clock"):
            # Load defaults if not present
            self.load_clock_defaults()
            return
        # Check validity of options
        for option in self.defaults["clock"]:
            fileval = self.settings["clock"].get(option, self.defaults["clock"][option])
            if fileval not in self.validity["clock"][option]:
                fileval = self.defaults["clock"][option]
            self.settings["clock"][option] = fileval

    def check_all_settings(self):
        self.check_clock_settings()

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
