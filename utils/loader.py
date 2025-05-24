# Import libraries
import yaml


# Class 'ConfLoader'
class ConfLoader:
    """ Class description """

    # Class initialization
    def __init__(self, filepath: str):
        """ Initializer description """
        self.filepath = filepath
        self.config = self.fetch()

    # Function 'fetch'
    def fetch(self) -> dict:
        """ Function description """
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Error: File '{self.filepath}' not found.")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            return {}

    # Function 'display'
    def display(self) -> None:
        """ Function description """
        main = self.config.get('main', {})
        filters = self.config.get('filters', {})
        trade = self.config.get('trade', {})
        priority = self.config.get('priority', {})

        print(f"Bot: {main.get('name', 'unamed')}")
        print(f"Listener: {filters.get('listener', 'not configured')}")
        print("Trade settings:")
        print(f"\t- Buy amount: {trade.get('buyamount', 'not configured')} SOL")
        slippage = trade.get('buyslippage')

        if slippage is not None:
            print(f"\t- Buy slippage: {slippage * 100}%")
        else:
            print("\t- Buy slippage: not configured")
        print(f"\t- Fast mode: {'enabled' if trade.get('fastmode') else 'disabled'}")

        print("Priority fees:")
        if priority.get('enabledynamic'):
            print("\t- Dynamic fees enabled")
        elif priority.get('enablefixed'):
            print(f"\t- Fixed fee: {priority.get('baselamports', 'not configured')} microlamports")

        print("Configuration loaded successfully")
