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
        # Main
        main = self.config.get('main', {})
        print("MAIN")
        print(f"[+] Status: {main.get('status', 'n/c')}")
        print(f"[+] Name: {main.get('name', 'n/c')}")
        print(f"[+] Sandbox: {main.get('sandbox', 'n/c')}")

        sandbox = main.get('sandbox')
        if sandbox is True:
            print(f"[+] Balance: {main.get('initbalance', '0')} SOL")

        print(f"[+] Max. Open Trades: {main.get('maxopentrades', 'n/c')}\n")

        # Monitoring
        monitoring = self.config.get('monitoring', {})
        print("MONITORING")
        print(f"[+] Listeners: {monitoring.get('chain', 'n/c')}\n")

        # Filters
        filters = self.config.get('filters', {})
        print("FILTERS")
        print(f"[+] Match String: {filters.get('matchstring', 'n/c')}")
        print(f"[+] Match Address: {filters.get('matchaddress', 'n/c')}")
        print(f"[+] No-Shorting: {filters.get('noshorting', 'n/c')}")
        print(f"[+] No-Stopping: {filters.get('nostopping', 'n/c')}\n")

        # Timing
        timing = self.config.get('timing', {})
        print("TIMING")
        print(f"[+] Token Initialization: {timing.get('tokenidleinit', 'n/c')}")
        print(f"[+] Token Sell Period: {timing.get('tokenidleshort', 'n/c')}")
        print(f"[+] Token New Detection: {timing.get('tokenidlenew', 'n/c')}")
        print(f"[+] Min. Token Age: {timing.get('tokenminage', 'n/c')}")
        print(f"[+] Max. Token Age: {timing.get('tokenmaxage', 'n/c')}")
        print(f"[+] Token Timeout: {timing.get('tokentimeout', 'n/c')}\n")

        # Trade
        trade = self.config.get('trade', {})
        print("TRADE")
        print(f"[+] Buy Amount: {trade.get('buyamount', '0')} SOL")
        print(f"[+] Buy Slippage: {trade.get('buyslippage', '0')} %")
        print(f"[+] Sell Slippage: {trade.get('sellslippage', '0')} %")
        print(f"[+] Fast Mode: {trade.get('fastmode', 'n/c')}")
        print(f"[+] Fast Tokens: {trade.get('fasttokens', '0')}")
        print(f"[+] Stop Loss: {trade.get('stoploss', '0')} %")
        print(f"[+] Take Profit: {trade.get('takeprofit', '0')} %")
        print(f"[+] Trailing Profit: {trade.get('trailprofit', 'n/c')}")
        print(f"[+] Trailing Level 1: {trade.get('trailone', 'n/c')}")
        print(f"[+] Trailing Level 2: {trade.get('trailtwo', 'n/c')}")
        print(f"[+] Trailing Level 3: {trade.get('trailthree', 'n/c')}")
        print(f"[+] Trailing Level 4: {trade.get('trailfour', 'n/c')}")
        print(f"[+] Trailing Level 5: {trade.get('trailfive', 'n/c')}")
        print(f"[+] Trade Count: {trade.get('countdown', 'n/c')}\n")

        # Priority
        priority = self.config.get('priority', {})
        print("PRIORITY")
        print(f"[+] Dynamic Priority: {priority.get('dynamic', 'n/c')}")
        print(f"[+] Fixed Fee: {priority.get('fixed', 'n/c')}")
        print(f"[+] Base Lamports: {priority.get('lamports', 'n/c')}")
        print(f"[+] Extra Percentage: {priority.get('extra', '0')}")
        print(f"[+] Hard Cap: {priority.get('hardcap', '0')}\n")

        # Retries
        retries = self.config.get('retries', {})
        print("RETRIES")
        print(f"[+] Max. Attempts: {retries.get('attempts', 'n/c')}\n")

        # Wipe
        wipe = self.config.get('wipe', {})
        print("WIPE")
        print(f"[+] Cleanup Mode: {wipe.get('clean', 'n/c')}")
        print(f"[+] Force Burn: {wipe.get('burn', 'n/c')}")
        print(f"[+] Priority Rate: {wipe.get('rate', 'n/c')}\n")

        # Rules
        rules = self.config.get('rules', {})
        print("RULES")
        print(f"[+] Min. Market Cap: {rules.get('minmarketcap', '0')} %")
        print(f"[+] Max. Market Cap: {rules.get('maxmarketcap', '0')} %")
        print(f"[+] Min. Market Volume: {rules.get('minmarketvol', '0')} %")
        print(f"[+] Max. Market Volume: {rules.get('maxmarketvol', '0')} %")
        print(f"[+] Min. Owner Hold: {rules.get('minholdowner', '0')} %")
        print(f"[+] Max. Owner Hold: {rules.get('maxholdowner', '0')} %")
        print(f"[+] Top Holder: {rules.get('topholders', 'n/c')}")
        print(f"[+] Min. Holders: {rules.get('minholders', 'n/c')}")
        print(f"[+] Max. Holders: {rules.get('maxholders', 'n/c')}")
        print(f"[+] Holders Check: {rules.get('holderscheck', 'n/c')}")
        print(f"[+] Holders Balance: {rules.get('holdersbalance', '0')} SOL")
        print(f"[+] Min. Liquidity Pool: {rules.get('minliquidity', '0')} USD")
        print(f"[+] Max. Liquidity Pool: {rules.get('maxliquidity', '0')} USD\n")
        print("---")
        print("Configuration loaded successfully")