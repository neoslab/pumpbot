# Import libraries
import asyncio
import logging
import multiprocessing

# Import packages
from pathlib import Path

# Import dependencies
from utils.loader import ConfLoader
from utils.logger import LogFormat
from handler.agent import PumpAgent


# Class 'PumpBotManager'
class PumpBotManager:
    """ Class description """

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
            apiendpoint = nodeinfo["api"],
            privatekey = loadwallet["privatekey"],

            # Main
            botstatus = botconf["main"]["status"],
            multithread = botconf["main"]["multithread"],
            sandbox = botconf["main"]["sandbox"],
            initbalance = botconf["main"]["initbalance"],
            opentrades = botconf["main"]["opentrades"],

            # Monitoring
            chainlistener = botconf["monitoring"]["chain"],

            # Filters
            matchstring = botconf["filters"]["matchstring"],
            matchaddress = botconf["filters"]["matchaddress"],
            noshorting = botconf["filters"]["noshorting"],
            filteroff = botconf["filters"]["filteroff"],

            # Timing:
            tokenidleinit = botconf["timing"]["tokenidleinit"],
            tokenidleshort = botconf["timing"]["tokenidleshort"],
            tokenidlenew = botconf["timing"]["tokenidlenew"],
            tokenminage = botconf["timing"]["tokenminage"],
            tokenmaxage = botconf["timing"]["tokenmaxage"],
            tokentimeout = botconf["timing"]["tokentimeout"],

            # Trade:
            buyamount = botconf["trade"]["buyamount"],
            buyslippage = botconf["trade"]["buyslippage"],
            sellslippage = botconf["trade"]["sellslippage"],
            fastmode = botconf["trade"]["fastmode"],
            fasttokens = botconf["trade"]["fasttokens"],
            stoploss = botconf["trade"]["stoploss"],
            takeprofit = botconf["trade"]["takeprofit"],
            trailprofit = botconf["trade"]["trailprofit"],
            tradetimeout = botconf["trade"]["timeout"],

            # Priority:
            priodynamic = botconf["priority"]["dynamic"],
            priofixed = botconf["priority"]["fixed"],
            priolamports = botconf["priority"]["lamports"],
            prioextrafee = botconf["priority"]["extra"],
            priohardcap = botconf["priority"]["hardcap"],

            # Retries:
            maxattempts = botconf["retries"]["attempts"],

            # Wipe:
            cleanall = botconf["wipe"]["clean"],
            cleanburn = botconf["wipe"]["burn"],
            cleanrate = botconf["wipe"]["rate"],

            # Rules:
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

    # Function 'botprocess'
    def botprocess(self, confpath: str):
        """ Function description """
        asyncio.run(self.startbot(confpath))

    # Function 'execbots'
    def execbots(self):
        """ Function description """
        if not self.botsdir.exists():
            logging.error(f"Bot directory '{self.botsdir}' not found")
            return

        botsdata = list(self.botsdir.glob("*.yaml"))
        if not botsdata:
            logging.error(f"No bot configuration files found in '{self.botsdir}'")
            return

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
                if botmain.get("multithread", False):
                    logging.info(f"Starting bot '{botname}' in {trademode} mode and multithread process")
                    process = multiprocessing.Process(
                        target=self.botprocess,
                        args=(str(botfile),),
                        name=f"bot-{botname}"
                    )
                    process.start()
                    self.processes.append(process)
                else:
                    logging.info(f"Starting bot '{botname}' in {trademode} mode and main process")
                    asyncio.run(self.startbot(str(botfile)))

            except Exception as e:
                logging.exception(f"Failed to start bot from {botfile}: {e}")

        logging.info(f"Started {len(botsdata) - self.skipbots} bots - skipped {self.skipbots} disabled bots")

        for process in self.processes:
            process.join()
            logging.info(f"Process {process.name} completed")

    # Function 'run'
    def run(self):
        """ Function description """
        print("Welcome to PumpBot")
        LogFormat.show()
        self.execbots()