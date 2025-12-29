# Import libraries
import logging

# Import packages
from pathlib import Path


# Class 'LogFormat'
class LogFormat(logging.Formatter):
    """ Class description """

    # Define 'colorcodes'
    colorcodes = {
        logging.DEBUG: "\033[90m",      # Grey
        logging.INFO: "\033[94m",       # Blue
        logging.WARNING: "\033[93m",    # Yellow
        logging.ERROR: "\033[91m",      # Red
        logging.CRITICAL: "\033[95m",   # Magenta
        logging.NOTSET: "\033[97m",     # White or default
    }

    # Define 'resetcode'
    resetcode = "\033[0m"

    # Function 'format'
    def format(self, record):
        """ Function description """
        logfmt = '%(asctime)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(logfmt, datefmt='%Y-%m-%d %H:%M:%S')
        formatted = formatter.format(record)
        color = self.colorcodes.get(record.levelno, "")
        return f"{color}{formatted}{self.resetcode}"

    # Function 'show'
    @staticmethod
    def show():
        """ Function description """
        handler = logging.StreamHandler()
        handler.setFormatter(LogFormat())
        logging.getLogger().handlers = [handler]
        logging.getLogger().setLevel(logging.INFO)

    # Function 'save'
    @staticmethod
    def save(botname: str):
        """ Function description """
        logdir = Path("logs")
        logdir.mkdir(exist_ok=True)
        log_file = logdir / f"{botname}.log"
        logger = logging.getLogger()

        if any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file) for h in logger.handlers):
            return

        logformat = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        logformat.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(logformat)