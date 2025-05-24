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
    def __init__(self, bots_directory: str = "bots"):
        """ Initializer description """
        self.botsdir = Path(bots_directory)
        self.processes = []
        self.skipbots = 0

    # Function 'startbot'
    @staticmethod
    async def startbot(confpath: str):
        """ Function description """
        loader = ConfLoader(confpath)
        botconf = loader.config
        LogFormat.save(botconf["main"]["name"])
        loader.display()

        agent = PumpAgent(
            rpcendpoint=botconf["main"]["rpcendpoint"],
            wssendpoint=botconf["main"]["wssendpoint"],
            privkey=botconf["main"]["privkey"],
            buyamount=botconf["trade"]["buyamount"],
            buyslippage=botconf["trade"]["buyslippage"],
            sellslippage=botconf["trade"]["sellslippage"],
            fastmode=botconf["trade"].get("fastmode", False),
            fasttokens=botconf["trade"].get("fasttokens", 30),
            listener=botconf["filters"]["listener"],
            geyserendpoint=botconf.get("geyser", {}).get("endpoint"),
            geyserapitoken=botconf.get("geyser", {}).get("apitoken"),
            geyserauthtype=botconf.get("geyser", {}).get("authtype"),
            prioritydynenabled=botconf.get("priority", {}).get("enabledynamic", False),
            priorityfixenabled=botconf.get("priority", {}).get("enablefixed", True),
            prioritybaselamports=botconf.get("priority", {}).get("baselamports", 500000),
            priorityextrafee=botconf.get("priority", {}).get("extrapercent", 0.0),
            priorityhardcap=botconf.get("priority", {}).get("hardcap", 500000),
            maxretries=botconf.get("retries", {}).get("maxattempts", 10),
            waitaftercreation=botconf.get("retries", {}).get("waitaftercreation", 15),
            waitafterbuy=botconf.get("retries", {}).get("waitafterbuy", 15),
            waitnewtoken=botconf.get("retries", {}).get("waitnewtoken", 15),
            maxtokenage=botconf.get("timing", {}).get("tokenmaxage", 0.001),
            waittokentimeout=botconf.get("timing", {}).get("tokentimeout", 30),
            cleanupmode=botconf.get("cleanup", {}).get("mode", "disabled"),
            cleanupburn=botconf.get("cleanup", {}).get("forceburn", False),
            cleanupfee=botconf.get("cleanup", {}).get("priorityfee", False),
            matchstring=botconf["filters"].get("matchstring"),
            useraddress=botconf["filters"].get("useraddress"),
            noshorting=botconf["filters"].get("noshorting", False),
            filteroff=botconf["filters"].get("filteroff", False),
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

                if not botmain.get("enabled", True):
                    logging.info(f"Skipping disabled bot '{botname}'")
                    self.skipbots += 1
                    continue

                mode = "sandbox" if botmain.get("sandbox", False) else "market"

                if botmain.get("separate", False):
                    logging.info(f"Starting bot '{botname}' in {mode} mode and separate process")
                    process = multiprocessing.Process(
                        target=self.botprocess,
                        args=(str(botfile),),
                        name=f"bot-{botname}"
                    )
                    process.start()
                    self.processes.append(process)
                else:
                    logging.info(f"Starting bot '{botname}' in {mode} mode and main process")
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