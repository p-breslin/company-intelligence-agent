import os
import configparser

"""ConfigLoader class to handle configuration loading from a .ini file."""

class ConfigLoader:
    def __init__(self):
        self.config = configparser.ConfigParser()

        # Determine config path
        self.config_path = os.getenv("DB_CONFIG_PATH", "configs/config.ini")

        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        self.config.read(self.config_path)

    def get_section(self, section):
        """Returns a dictionary of the specified section."""
        if section not in self.config:
            raise KeyError(f"Section [{section}] not found in config file")
        return dict(self.config[section])

    def get(self, section, key):
        """Returns a single value from the specified section."""
        return self.config.get(section, key)


# Create a global instance to be imported anywhere
config = ConfigLoader()