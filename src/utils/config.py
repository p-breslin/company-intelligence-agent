import os
import json

"""ConfigLoader class to handle configuration loading from a JSON file."""

class ConfigLoader:
    def __init__(self):
        # Determine config path
        self.config_path = os.getenv("DB_CONFIG_PATH", "configs/config.json")

        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        # Load the JSON config
        with open(self.config_path, "r") as f:
            self.config = json.load(f)

    def get_section(self, section):
        """Returns a dictionary of the specified section."""
        if section not in self.config:
            raise KeyError(f"Section [{section}] not found in config file")
        return dict(self.config[section])

    def get(self, section, key):
        """Returns a single value from the specified section."""
        if section not in self.config or key not in self.config[section]:
            raise KeyError(f"Key '{key}' not found in section '{section}'")
        return self.config[section][key]


# Create a global instance to be imported anywhere
config = ConfigLoader()