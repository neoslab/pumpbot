# Import libraries
import yaml


# Function 'ConfigBot'
def ConfigBot(filepath):
    """
    This function loads and parses a YAML configuration file from the specified path into a Python dictionary.
    It ensures that if the file is empty or unreadable as YAML, an empty dictionary is returned as a safe fallback.
    This function is commonly used to import bot settings into the application for manipulation, inspection,
    or execution. It assumes UTF-8 encoding for compatibility and uniformity.

    Parameters:
    - filepath (str): The full or relative path to the YAML configuration file to be loaded.

    Returns:
    - dict: A dictionary representing the YAML file content, or an empty dictionary if the file is empty or invalid.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# Function 'ConfigPrint'
def ConfigPrint(config: dict) -> None:
    """
    This function prints a human-readable summary of a bot’s configuration to the standard output.
    It extracts and displays key sections including bot name, listener settings, trade parameters
    (like amount, slippage, and fast mode), and priority fee configurations. The output is intended
    for debugging or confirmation of settings before launching a bot. It is read-only and does not
    modify the input dictionary.

    Parameters:
    - config (dict): A dictionary containing bot configuration values, typically loaded from a YAML file.

    Returns:
    - None
    """
    print(f"Bot: {config.get('main', {}).get('name', 'unamed')}")
    print(f"Listener: {config.get('filters', {}).get('listener', 'not configured')}")
    trade = config.get('trade', {})
    print("Trade settings:")
    print(f"\t- Buy amount: {trade.get('buyamount', 'not configured')} SOL")
    print(f"\t- Buy slippage: {trade.get('buyslippage', 'not configured') * 100}%")
    print(f"\t- Fast mode: {'enabled' if trade.get('fastmode') else 'disabled'}")
    fees = config.get('priority', {})
    print("Priority fees:")
    if fees.get('enabledynamic'):
        print("\t- Dynamic fees enabled")
    elif fees.get('enablefixed'):
        print(f"\t- Fixed fee: {fees.get('baselamports', 'not configured')} microlamports")
    print("Configuration loaded successfully")