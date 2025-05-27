# Import libraries
import asyncio
import logging
import time
from pathlib import Path

# Import packages
from utils.loader import ConfLoader
from utils.logger import LogFormat
from utils.loop import set_event_loop
from handler.agent import PumpAgent
set_event_loop()

# Class 'PumpBotManager'
class PumpBotManager:
    """Manager to load and execute Pump trading bots."""

    # Class initialization
    def __init__(self, botspath: str = "bots"):
        """ Initializer description """
        self.botsdir = Path(botspath)
        self.processes = []
        self.skipbots = 0

    # Function 'startbot'
    @staticmethod
    async def startbot(confpath: str):
        """ Function description """
        nodeinfo = ConfLoader.endpoint()
        loadwallet = ConfLoader.wallet()

        # Load config
        loadbot = ConfLoader(confpath)
        botconf = loadbot.config
        LogFormat.save(botconf["main"]["name"])
        loadbot.display()

        agent = PumpAgent(
            # General
            rpcendpoint = nodeinfo["rpc"],
            wssendpoint = nodeinfo["wss"],
            privatekey = loadwallet["privatekey"],

            # Main
            sandbox = botconf["main"]["sandbox"],
            initbalance = botconf["main"]["initbalance"],
            maxopentrades = botconf["main"]["maxopentrades"],

            # Monitoring
            chainlistener = botconf["monitoring"]["chain"],

            # Filters
            matchstring = botconf["filters"]["matchstring"],
            matchaddress = botconf["filters"]["matchaddress"],
            noshorting = botconf["filters"]["noshorting"],
            nostopping = botconf["filters"]["nostopping"],

            # Timing
            tokenidleinit = botconf["timing"]["tokenidleinit"],
            tokenidleshort = botconf["timing"]["tokenidleshort"],
            tokenidlenew = botconf["timing"]["tokenidlenew"],
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
            countdown = botconf["trade"]["countdown"],

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

        await agent.AgentStart()

    # Function 'execbots'
    def execbots(self):
        """ Function description """
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

        # Wait for all subprocesses to finish
        for process in self.processes:
            process.join()
            logging.info(f"Process {process.name} completed")

        return True

    # Function 'run'
    def run(self):
        """ Function description """
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
                logging.error(f"Error: {e}")
                time.sleep(1)


# Function 'def main():"
def main():
    """ Function description """
    bot = PumpBotManager()
    bot.run()


# Main callback
if __name__ == '__main__':
    """ Function description """
    main()


