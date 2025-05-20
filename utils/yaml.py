# Import libraries
import yaml


# Class 'QuotedDumper'
class QuotedDumper(yaml.SafeDumper):
    """
    This class is a customized extension of PyYAML’s SafeDumper class, designed to alter the way
    scalar values are represented when YAML data is serialized. By subclassing `yaml.SafeDumper`,
    it allows for the injection of custom representers that enforce specific output styles—such as
    quoting strings or formatting booleans and nulls in a standardized way. It plays a critical role
    in ensuring consistent and readable YAML output for configuration files.

    Parameters:
    - Inherits from yaml.SafeDumper; does not accept additional arguments directly.

    Returns:
    - None
    """
    pass


# Function 'QuotedScalar'
def QuotedScalar(dumper, data):
    """
    This function defines a custom representer for string values when using the `QuotedDumper`
    subclass of PyYAML. It ensures that all string values are serialized with explicit double quotes
    (e.g., `"value"`), which helps avoid ambiguities during parsing or downstream processing.
    This behavior is especially important for configuration files that may contain strings resembling
    other data types, such as "true", "null", or numbers.

    Parameters:
    - dumper (yaml.Dumper): The dumper instance used by PyYAML during serialization.
    - data (str): The string data to be represented as a quoted YAML scalar.

    Returns:
    - yaml.ScalarNode: A YAML node representing the quoted scalar string.
    """
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')


# Function 'SaveYAML'
def SaveYAML(filepath, data):
    """
    This function handles writing Python dictionaries (or other YAML-serializable objects) to a
    YAML file with customized formatting. It uses a custom dumper (`QuotedDumper`) to ensure
    consistent quoting of strings, formatting of booleans as "True"/"False", and explicit null
    values. The function simplifies YAML file creation with readable and predictable output
    formatting, especially useful for user-editable config files.

    Parameters:
    - filepath (str): The absolute or relative path to the file where YAML content will be written.
    - data (dict): The structured Python data (usually nested dictionaries/lists) to serialize as YAML.

    Returns:
    - None
    """
    with open(filepath, 'w') as f:
        yaml.dump(data, f, sort_keys=False, Dumper=QuotedDumper)


# Attach representers to the custom dumper
QuotedDumper.add_representer(str, QuotedScalar)
QuotedDumper.add_representer(type(None), lambda s, d: s.represent_scalar('tag:yaml.org,2002:null', 'Null'))
QuotedDumper.add_representer(bool, lambda s, d: s.represent_scalar('tag:yaml.org,2002:bool', 'True' if d else 'False'))