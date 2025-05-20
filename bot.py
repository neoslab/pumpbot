# Import libraries
import asyncio
import logging
import multiprocessing

# Import packages
from pathlib import Path

# Import local packages
from config.loader import ConfigBot, ConfigPrint
from handler.agent import PumpAgent
from utils.logger import LogShow, LogSave


# Function 'BotStart"
async def BotStart(confpath: str):
    """
    This asynchronous function initializes and launches a PumpAgent instance based on a YAML configuration file path.
    It loads and parses the bot configuration, sets up logging for the bot name, prints configuration details,
    and initializes a trading agent using all extracted configuration parameters including endpoints, keys,
    trading parameters, filters, priority fee settings, retry policies, and optional modules such as Geyser.
    After preparing the agent with full configuration, it asynchronously starts the trading logic through the
    AgentStart() coroutine method on the PumpAgent instance.

    Parameters:
    - confpath (str): The full file path to the bot's YAML configuration file, used to load all operational parameters.

    Returns:
    - None
    """
    botconf = ConfigBot(confpath)
    LogSave(botconf["main"]["name"])
    ConfigPrint(botconf)
    agent = PumpAgent(
        # Connection settings
        rpcendpoint = botconf["main"]["rpcendpoint"],
        wssendpoint = botconf["main"]["wssendpoint"],
        privkey = botconf["main"]["privkey"],

        # Trade parameters
        buyamount = botconf["trade"]["buyamount"],
        buyslippage = botconf["trade"]["buyslippage"],
        sellslippage = botconf["trade"]["sellslippage"],

        # Fast mode settings
        fastmode = botconf["trade"].get("fastmode", False),
        fasttokens = botconf["trade"].get("fasttokens", 30),

        # Listener configuration
        listener = botconf["filters"]["listener"],

        # Geyser configuration (if applicable)
        geyserendpoint = botconf.get("geyser", {}).get("endpoint"),
        geyserapitoken = botconf.get("geyser", {}).get("apitoken"),
        geyserauthtype = botconf.get("geyser", {}).get("authtype"),

        # Priority fee configuration
        prioritydynenabled = botconf.get("priority", {}).get("enabledynamic", False),
        priorityfixenabled = botconf.get("priority", {}).get("enablefixed", True),
        prioritybaselamports = botconf.get("priority", {}).get("baselamports", 500000),
        priorityextrafee = botconf.get("priority", {}).get("extrapercent", 0.0),
        priorityhardcap = botconf.get("priority", {}).get("hardcap", 500000),

        # Retry and timeout settings
        maxretries = botconf.get("retries", {}).get("maxattempts", 10),
        waitaftercreation = botconf.get("retries", {}).get("waitaftercreation", 15),
        waitafterbuy = botconf.get("retries", {}).get("waitafterbuy", 15),
        waitnewtoken = botconf.get("retries", {}).get("waitnewtoken", 15),
        maxtokenage = botconf.get("timing", {}).get("tokenmaxage", 0.001),
        waittokentimeout = botconf.get("timing", {}).get("tokentimeout", 30),

        # Cleanup settings
        cleanupmode = botconf.get("cleanup", {}).get("mode", "disabled"),
        cleanupburn = botconf.get("cleanup", {}).get("forceburn", False),
        cleanupfee = botconf.get("cleanup", {}).get("priorityfee", False),

        # Trading filters
        matchstring = botconf["filters"].get("matchstring"),
        useraddress = botconf["filters"].get("useraddress"),
        noshorting = botconf["filters"].get("noshorting", False),
        filteroff = botconf["filters"].get("filteroff", False),
    )

    await agent.AgentStart()


# Function 'BotProcess"
def BotProcess(confpath: str):
    """
    This function serves as a synchronous wrapper to launch the asynchronous BotStart routine
    within a separate OS-level process. It is designed for multiprocessing use cases where
    each bot instance runs independently from others. The configuration path is passed
    to the coroutine using asyncio.run(), which ensures the async logic executes fully in
    isolation, making it ideal for concurrent bot operations without event loop conflicts.

    Parameters:
    - confpath (str): A string representing the path to the YAML configuration file for the bot.

    Returns:
    - None
    """
    asyncio.run(BotStart(confpath))


# Function 'BotExec'
def BotExec():
    """
    This function orchestrates the discovery and execution of all bot configuration files
    located in the "bots" directory. It validates the presence of configuration files,
    loads each YAML configuration, checks whether the bot is enabled or requires isolated
    execution via multiprocessing, and starts it accordingly. Disabled bots are skipped with
    logs, and execution errors are gracefully handled with logging for troubleshooting.

    Parameters:
    - None

    Returns:
    - None
    """
    botsdir = Path("bots")
    if not botsdir.exists():
        logging.error(f"Bot directory '{botsdir}' not found")
        return

    botsdata = list(botsdir.glob("*.yaml"))
    if not botsdata:
        logging.error(f"No bot configuration files found in '{botsdir}'")
        return

    logging.info(f"Found {len(botsdata)} bot configuration files")
    processes = []
    skipbots = 0

    for botfile in botsdata:
        try:
            botconf = ConfigBot(str(botfile))
            botmain = botconf.get("main", {})
            botname = botmain.get("name", botfile.stem)

            if not botmain.get("enabled", True):
                logging.info(f"Skipping disabled bot '{botname}'")
                skipbots += 1
                continue

            # If bot should run in a separate process
            if botmain.get("separate", False):
                mode = "sandbox" if botmain.get("sandbox", False) else "market"
                logging.info(f"Starting bot '{botname}' in {mode} mode and separate process")
                process = multiprocessing.Process(target=BotProcess, args=(str(botfile),), name=f"bot-{botname}")
                process.start()
                processes.append(process)
            else:
                # Run bot in the main process
                mode = "sandbox" if botmain.get("sandbox", False) else "market"
                logging.info(f"Starting bot '{botname}' in {mode} mode and main process")
                asyncio.run(BotStart(str(botfile)))

        except Exception as e:
            logging.exception(f"Failed to start bot from {botfile}: {e}")

    logging.info(f"Started {len(botsdata) - skipbots} bots - skipped {skipbots} disabled bots")
    for process in processes:
        process.join()
        logging.info(f"Process {process.name} completed")


# Function 'MainExec'
def MainExec():
    """
    This function serves as the entry point for the bot execution system.
    It prints a welcome message to the console, initializes the logging display
    via LogShow(), and calls BotExec() to scan and launch all available bot configurations.
    This is the central bootstrap routine that ties together logging, configuration loading,
    and bot initialization into a single user-facing starting point.

    Parameters:
    - None

    Returns:
    - None
    """
    print("Welcome to PumpBot")
    LogShow()
    BotExec()


# Main callback
if __name__ == "__main__":
    """
    This conditional block ensures that the script only runs the main execution
    routine when executed directly as a standalone program. It prevents unintended
    execution when the module is imported elsewhere. When triggered, it invokes
    the MainExec() function to begin bot loading, configuration parsing, and process
    management as defined in the main orchestration logic.

    Parameters:
    - None

    Returns:
    - None
    """
    MainExec()
