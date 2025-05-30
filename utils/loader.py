# === Import libraries ===
import yaml

# === Import packages ===
from pathlib import Path


# === Class 'ConfLoader' ===
class ConfLoader:
    """
    This class is responsible for loading and parsing YAML configuration files used by the bot system.
    It can load specific bot configurations, retrieve common system-wide settings such as endpoints and wallet info,
    and display key information for debugging and validation purposes. It is intended to be instantiated with
    a path to a bot-specific YAML file and serves as a unified configuration access point throughout the project.

    Parameters:
    - filepath (str): Path to the YAML configuration file to be loaded and parsed.

    Returns:
    - None
    """

    # === Function '__init__' ===
    def __init__(self, filepath: str):
        """
        The initializer sets up a new instance of ConfLoader, loading the YAML configuration
        located at the specified file path. Upon initialization, it immediately parses the
        contents of the file using the internal `fetch` method and stores the result in
        the `config` attribute for further use by other components of the bot system.

        Parameters:
        - filepath (str): Path to the YAML file to be loaded.

        Returns:
        - None
        """
        self.filepath = filepath
        self.config = self.fetch()

    # === Function 'fetch' ===
    def fetch(self) -> dict:
        """
        Opens and reads the YAML configuration file provided during initialization. It attempts
        to load the file using the PyYAML library with UTF-8 encoding and converts the result
        into a dictionary. If the file is not found or contains invalid YAML, it handles the
        error gracefully and returns an empty dictionary instead of halting execution.

        Parameters:
        - None

        Returns:
        - dict: A dictionary representing the loaded YAML configuration. Returns an empty dict on error.
        """
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Error: File '{self.filepath}' not found.")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            return {}

    # === Function 'endpoint' ===
    @staticmethod
    def endpoint() -> dict:
        """
        Loads the `config/endpoint.yaml` file which contains the global RPC and WSS endpoints
        for blockchain communication. This static method is used by multiple components needing
        access to node configuration. If the file is missing or invalid, it returns an empty
        dictionary and prints a corresponding message for debugging.

        Parameters:
        - None

        Returns:
        - dict: A dictionary containing keys like 'rpc' and 'wss' or an empty dict on error.
        """
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

    # === Function 'wallet' ===
    @staticmethod
    def wallet() -> dict:
        """
        Loads the `config/wallet.yaml` file containing the private key used by bots for
        signing transactions. This method ensures secure access to wallet credentials
        for system-wide use. If the file is missing or improperly formatted, it returns
        an empty dictionary and logs a warning to the console.

        Parameters:
        - None

        Returns:
        - dict: A dictionary with at least a 'privatekey' entry, or an empty dict on error.
        """
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

    # === Function 'display' ===
    def display(self) -> None:
        """
        Displays the loaded configuration in a structured and human-readable format.
        The function retrieves details from the endpoint, wallet, and all relevant
        configuration sections (e.g., main, monitoring, filters, timing, trade, etc.).
        It outputs each block with labels and values to help users verify correctness
        and completeness of their bot’s YAML file before execution.

        Parameters:
        - None

        Returns:
        - None
        """
        # Define 'main'
        main = self.config.get('main', {})

        # Define 'endpoint'
        endpoint = self.endpoint()

        # Define 'wallet'
        wallet = self.wallet()

        # Define 'monitoring'
        monitoring = self.config.get('monitoring', {})

        # Define 'filters'
        filters = self.config.get('filters', {})

        # Define 'timing'
        timing = self.config.get('timing', {})

        # Define 'trade'
        trade = self.config.get('trade', {})

        # Define 'priority'
        priority = self.config.get('priority', {})

        # Define 'retries'
        retries = self.config.get('retries', {})

        # Define 'wipe'
        wipe = self.config.get('wipe', {})

        # Define 'rules'
        rules = self.config.get('rules', {})

        print("-" * 60)
        print(f"BOTNAME: {main.get('botname', 'n/c')}")
        print("-" * 60)

        # === Endpoint ===
        print("ENDPOINT")
        print(f"[+] RPC Endpoint: {endpoint.get('rpc', 'n/c')}")
        print(f"[+] WSS Endpoint: {endpoint.get('wss', 'n/c')}")
        print("-" * 60)

        # === Wallet ===
        privdatekey = wallet.get('privatekey', 'n/c')
        from core.wallet import Wallet
        try:
            wallet_obj = Wallet(privdatekey)
            publickey = wallet_obj.pubkey if wallet_obj.validprikey else "Invalid"
        except (ValueError, TypeError) as e:
            publickey = f"Invalid ({type(e).__name__})"

        print("WALLET")
        print(f"[+] Public Address: {publickey}")
        print(f"[+] Private Key: {privdatekey}")
        print("-" * 60)

        # === Main ===
        print("MAIN")
        print(f"[+] Status: {main.get('status', 'n/c')}")
        print(f"[+] Sandbox: {main.get('sandbox', 'n/c')}")

        sandbox = main.get('sandbox')
        if sandbox is True:
            print(f"[+] Balance: {main.get('initbalance', '0')} SOL")

        print(f"[+] Max. Open Trades: {main.get('maxopentrades', 'n/c')}")
        print("-" * 60)

        # === Monitoring ===
        print("MONITORING")
        print(f"[+] Listeners: {monitoring.get('chain', 'n/c')}")
        print(f"[+] Interval: {monitoring.get('interval', 'n/c')}")
        print("-" * 60)

        # === Filters ===
        print("FILTERS")
        print(f"[+] Match String: {filters.get('matchstring', 'n/c')}")
        print(f"[+] Match Address: {filters.get('matchaddress', 'n/c')}")
        print(f"[+] No-Shorting: {filters.get('noshorting', 'n/c')}")
        print(f"[+] No-Stopping: {filters.get('nostopping', 'n/c')}")
        print("-" * 60)

        # === Timing ===
        print("TIMING")
        print(f"[+] Token Initialization: {timing.get('tokenidleinit', 'n/c')}")
        print(f"[+] Token Sell Period: {timing.get('tokenidleshort', 'n/c')}")
        print(f"[+] Token Fresh Detection: {timing.get('tokenidlefresh', 'n/c')}")
        print(f"[+] Min. Token Age: {timing.get('tokenminage', 'n/c')}")
        print(f"[+] Max. Token Age: {timing.get('tokenmaxage', 'n/c')}")
        print(f"[+] Token Timeout: {timing.get('tokentimeout', 'n/c')}")
        print("-" * 60)

        # === Trade ===
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
        print("-" * 60)

        # === Priority ===
        print("PRIORITY")
        print(f"[+] Dynamic Priority: {priority.get('dynamic', 'n/c')}")
        print(f"[+] Fixed Fee: {priority.get('fixed', 'n/c')}")
        print(f"[+] Base Lamports: {priority.get('lamports', 'n/c')}")
        print(f"[+] Extra Percentage: {priority.get('extra', '0')}")
        print(f"[+] Hard Cap: {priority.get('hardcap', '0')}")
        print("-" * 60)

        # === Retries ===
        print("RETRIES")
        print(f"[+] Max. Attempts: {retries.get('attempts', 'n/c')}")
        print("-" * 60)

        # === Wipe ===
        print("WIPE")
        print(f"[+] Cleanup Mode: {wipe.get('clean', 'n/c')}")
        print(f"[+] Force Burn: {wipe.get('burn', 'n/c')}")
        print(f"[+] Priority Rate: {wipe.get('rate', 'n/c')}")
        print("-" * 60)

        # === Rules ===
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
        print(f"[+] Max. Liquidity Pool: {rules.get('maxliquidity', '0')} USD")
        print("-" * 60 + "\n")