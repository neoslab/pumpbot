# Import libraries
import yaml

# Import packages
from pathlib import Path


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

    # Function 'endpoint'
    @staticmethod
    def endpoint() -> dict:
        """ Function description """
        path = Path("config/endpoint.yaml")
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                print(f"Error parsing endpoint.yaml: {e}")
        else:
            print("config/endpoint.yaml not found.")
        return {}

    # Function 'wallet'
    @staticmethod
    def wallet() -> dict:
        """ Function description """
        path = Path("config/wallet.yaml")
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                print(f"Error parsing wallet.yaml: {e}")
        else:
            print("config/wallet.yaml not found.")
        return {}

    # Function 'display'
    def display(self) -> None:
        """ Function description """
        main = self.config.get('main', {})
        filters = self.config.get('filters', {})
        trade = self.config.get('trade', {})
        priority = self.config.get('priority', {})

        print(f"Bot: {main.get('name', 'unamed')}")
        print(f"Listener: {filters.get('chainlistener', 'not configured')}")
        print("Trade settings:")
        print(f"\t- Buy amount: {trade.get('buyamount', 'not configured')} SOL")
        slippage = trade.get('buyslippage')

        if slippage is not None:
            print(f"\t- Buy slippage: {slippage * 100}%")
        else:
            print("\t- Buy slippage: not configured")
        print(f"\t- Fast mode: {'enabled' if trade.get('fastmode') else 'disabled'}")

        print("Priority fees:")
        if priority.get('dynamic'):
            print("\t- Dynamic fees enabled")
        elif priority.get('fixed'):
            print(f"\t- Fixed fee: {priority.get('baselamports', 'not configured')} microlamports")

        # Load and display endpoint
        endpoint = self.endpoint()
        print("RPC/Endpoint config:")
        print(f"\t- RPC: {endpoint.get('rpc', 'not configured')}")
        print(f"\t- WSS: {endpoint.get('wss', 'not configured')}")
        print(f"\t- API: {endpoint.get('api', 'not configured')}")

        # Load and display wallet
        wallet = self.wallet()
        print("Wallet config:")
        print(f"\t- Public Address: {wallet.get('pubadd', 'not configured')}")
        print(f"\t- Private Key: {wallet.get('prikey', 'not configured')}")
        print("Configuration loaded successfully")
