import os
import json

"""ConfigLoader class to handle configuration loading from a JSON file."""

class ConfigLoader:
    def __init__(self):
        # Determine config path
        self.root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        self.config_path = os.getenv("DB_CONFIG_PATH", os.path.join(self.root, "configs/config.json"))

        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        # Load the JSON config
        with open(self.config_path, "r") as f:
            self.config = json.load(f)

    def get_section(self, section):
        """Returns a dictionary of the specified section."""
        if section not in self.config:
            raise KeyError(f"Section [{section}] not found in config file")
        section_data = dict(self.config[section])

        # If accessing the ChromaDB section, resolve the path dynamically
        if section == "chroma" and "root" in section_data:
            section_data["root"] = os.path.abspath(os.path.join(self.root, section_data["root"]))

        return section_data

    def get(self, section, key):
        """Returns a single value from the specified section."""
        if section not in self.config or key not in self.config[section]:
            raise KeyError(f"Key '{key}' not found in section '{section}'")
        return self.config[section][key]
    
    def get_list(self, key):
        """Returns a list from the JSON config."""
        if key not in self.config or not isinstance(self.config[key], list):
            raise KeyError(f"Key '{key}' not found or is not a list in config file")
        return self.config[key]


# Create a global instance to be imported anywhere
config = ConfigLoader()