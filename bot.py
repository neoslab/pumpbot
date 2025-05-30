# === Import libraries ===
import asyncio
import logging
import time
import sys

# === Import packages ===
from pathlib import Path

# === Import dependencies ===
from core.wallet import Wallet
from utils.loader import ConfLoader
from utils.logger import LogFormat
from utils.event import EventLoopConf
from handler.agent import PumpAgent

# === Execute 'EventLoopConf' ===
EventLoopConf.importlib()


# === Class 'ConfLoader' ===
class PumpBotManager:
    """
    This class manages the orchestration and lifecycle of multiple trading bot instances
    defined in YAML configuration files located in a specified directory. It handles bot
    validation, configuration loading, execution control, and continuous restart logic.
    Designed to be the main entry point for managing concurrent or repeated bot launches
    in a structured and automated environment.

    Parameters:
    - botspath (str): A string path to the folder where YAML bot configuration files are located.

    Returns:
    - None
    """

    # === Function '__init__' ===
    def __init__(self, botspath: str = "bots"):
        """
        Initializes the PumpBotManager by preparing internal structures for tracking bot
        processes and skipped entries. This initializer sets the directory path to locate
        YAML bot configuration files and initializes the process tracking list and counters.
        The manager is then ready to scan and execute the bots.

        Parameters:
        - botspath (str): Path to the directory containing bot configuration files in YAML format.

        Returns:
        - None
        """
        self.botsdir = Path(botspath)
        self.processes = []
        self.skipbots = 0

    # === Function 'startbot' ===
    @staticmethod
    async def startbot(confpath: str):
        """
        Asynchronously initializes and launches a single bot instance based on the provided
        configuration path. It loads the RPC/WSS node info, wallet credentials, and bot
        settings, validates the private key, and constructs a PumpAgent using all relevant
        parameters. The bot is then launched via its AgentStart() coroutine.

        Parameters:
        - confpath (str): The file path to the YAML configuration for a specific bot.

        Returns:
        - None
        """
        # Load node info
        nodeinfo = ConfLoader.endpoint()

        # Load wallet details
        loadwallet = ConfLoader.wallet()

        # Validate wallet before anything else
        testwallet = Wallet(loadwallet["privatekey"])
        if not testwallet.validprikey:
            logging.error("Invalid private key - Aborting bot execution.")
            sys.exit(1)

        # Load config
        loadbot = ConfLoader(confpath)
        botconf = loadbot.config
        LogFormat.save(botconf["main"]["botname"])

        agent = PumpAgent(
            # General
            rpcendpoint = nodeinfo["rpc"],
            wssendpoint = nodeinfo["wss"],
            privatekey = loadwallet["privatekey"],

            # Main
            botname = botconf["main"]["botname"],
            sandbox = botconf["main"]["sandbox"],
            initbalance = botconf["main"]["initbalance"],
            maxopentrades = botconf["main"]["maxopentrades"],

            # Monitoring
            chainlistener = botconf["monitoring"]["chain"],
            chaininterval = botconf["monitoring"]["interval"],

            # Filters
            matchstring = botconf["filters"]["matchstring"],
            matchaddress = botconf["filters"]["matchaddress"],
            noshorting = botconf["filters"]["noshorting"],
            nostopping = botconf["filters"]["nostopping"],

            # Timing
            tokenidleinit = botconf["timing"]["tokenidleinit"],
            tokenidleshort = botconf["timing"]["tokenidleshort"],
            tokenidlefresh = botconf["timing"]["tokenidlefresh"],
            tokenminage = botconf["timing"]["tokenminage"],
            tokenmaxage = botconf["timing"]["tokenmaxage"],
            tokentimeout = botconf["timing"]["tokentimeout"],

            # Trade
            buyamount = botconf["trade"]["buyamount"],
            buyslippage = botconf["trade"]["buyslippage"],
            sellslippage = botconf["trade"]["sellslippage"],
            fastmode = botconf["trade"]["fastmode"],
            fasttokens = botconf["trade"]["fasttokens"],
            stoploss = botconf["trade"]["stoploss"],
            takeprofit = botconf["trade"]["takeprofit"],
            trailprofit = botconf["trade"]["trailprofit"],

            # Priorities
            priodynamic = botconf["priority"]["dynamic"],
            priofixed = botconf["priority"]["fixed"],
            priolamports = botconf["priority"]["lamports"],
            prioextrafee = botconf["priority"]["extra"],
            priohardcap = botconf["priority"]["hardcap"],

            # Retries
            maxattempts = botconf["retries"]["attempts"],

            # Wipe
            cleanall = botconf["wipe"]["clean"],
            cleanburn = botconf["wipe"]["burn"],
            cleanrate = botconf["wipe"]["rate"],

            # Rules
            minmarketcap = botconf["rules"]["minmarketcap"],
            maxmarketcap = botconf["rules"]["maxmarketcap"],
            minmarketvol = botconf["rules"]["minmarketvol"],
            maxmarketvol = botconf["rules"]["maxmarketvol"],
            minholdowner = botconf["rules"]["minholdowner"],
            maxholdowner = botconf["rules"]["maxholdowner"],
            topholders = botconf["rules"]["topholders"],
            minholders = botconf["rules"]["minholders"],
            maxholders = botconf["rules"]["maxholders"],
            holderscheck = botconf["rules"]["holderscheck"],
            holdersbalance = botconf["rules"]["holdersbalance"],
            minliquidity = botconf["rules"]["minliquidity"],
            maxliquidity = botconf["rules"]["maxliquidity"]
        )

        await agent.agentstart()

    # === Function 'execbots' ===
    def execbots(self):
        """
        Iterates over all bot configuration files found in the configured directory. For
        each valid configuration, it checks if the bot is enabled and launches it using
        `startbot`. Keeps track of how many bots were skipped and logs execution details.
        Handles errors gracefully and aggregates execution status for logging.

        Parameters:
        - None

        Returns:
        - bool: True if at least one bot was successfully started, False otherwise.
        """
        if not self.botsdir.exists():
            logging.warning(f"Bot directory '{self.botsdir}' not found")
            return False

        botsdata = list(self.botsdir.glob("*.yaml"))
        if not botsdata:
            logging.warning(f"No bot configuration files found in '{self.botsdir}'")
            return False

        logging.info(f"Found {len(botsdata)} bot configuration files")
        for botfile in botsdata:
            try:
                botconf = ConfLoader(str(botfile)).config
                botmain = botconf.get("main", {})
                botname = botmain.get("name", botfile.stem)

                if not botmain.get("status", True):
                    logging.info(f"Skipping disabled bot '{botname}'")
                    self.skipbots += 1
                    continue

                trademode = "sandbox" if botmain.get("sandbox", False) else "market"
                logging.info(f"Starting bot '{botname}' in {trademode} mode")
                asyncio.run(self.startbot(str(botfile)))

            except Exception as e:
                logging.exception(f"Failed to start bot from {botfile}: {e}")

        logging.info(f"Started {len(botsdata) - self.skipbots} bots - skipped {self.skipbots} disabled bots")

        for process in self.processes:
            process.join()
            logging.info(f"Process {process.name} completed")

        return True

    # === Function 'run' ===
    def run(self):
        """
        Initiates the perpetual bot management loop, displaying logging configuration and
        continuously invoking the `execbots` method in a timed loop. This function ensures
        that bots are relaunched periodically and that system-level errors during execution
        cause a clean exit with logging for diagnostics.

        Parameters:
        - None

        Returns:
        - None
        """
        LogFormat.show()
        while True:
            try:
                self.processes.clear()
                self.skipbots = 0

                success = self.execbots()
                if success:
                    logging.info("All bots executed successfully. Restarting loop shortly...")
                else:
                    logging.info("No bots found or launched. Retrying...")

                time.sleep(5)
            except (RuntimeError, ValueError) as e:
                logging.error(f"Fatal error in run loop: {e}")
                sys.exit(1)


# === Function 'main' ===
def main():
    """
    Serves as the main entry point for initializing and running the PumpBotManager system.
    It first checks for the existence of the 'bots' directory and iterates over all YAML
    files found within, loading and displaying each configuration using ConfLoader. This
    provides visual confirmation of the loaded bot settings. After configuration validation,
    it instantiates the PumpBotManager and launches its perpetual execution loop to manage
    all available bots in the system.

    Parameters:
    - None

    Returns:
    - None
    """
    botsdir = Path("bots")
    if not botsdir.exists():
        logging.warning("Bots directory not found.")
    else:
        for botfile in botsdir.glob("*.yaml"):
            try:
                config = ConfLoader(str(botfile))
                config.display()
            except Exception as e:
                logging.error(f"Failed to load or display config from {botfile}: {e}")

    bot = PumpBotManager()
    bot.run()


# === Callback ===
if __name__ == '__main__':
    """ 
    Entry point when the script is executed directly. Triggers the `main()` function 
    to launch the PumpBotManager instance. This ensures that the bot orchestration 
    process only starts when this script is not imported as a module but run as the 
    main process.

    Parameters:
    - None

    Returns:
    - None
    """
    main()