# Import libraries
import logging

# Import packages
from datetime import datetime
from pathlib import Path


# Class 'LogFormat'
class LogFormat(logging.Formatter):
    """
    This class defines a custom log formatter with color-coded output for enhanced
    readability in terminal environments. Each log level is assigned a distinct
    ANSI color code to visually differentiate between debug, info, warning, error,
    and critical messages. The formatter wraps each formatted log message with
    the appropriate color code prefix and a reset code suffix, ensuring clean and
    consistent display. It is intended for use with stream handlers that support
    ANSI escape sequences, typically in console-based interfaces.

    Parameters:
    - Inherits from logging.Formatter, no additional instantiation parameters required.

    Returns:
    - None
    """

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
        """
        Formats a log record by applying a standard timestamped format string and
        dynamically injecting ANSI color codes based on the severity level of the log.
        The message is first formatted using the base logging.Formatter, then colorized
        using predefined ANSI sequences for visual differentiation. This is ideal for
        real-time console outputs where quick identification of log severity is helpful.

        Parameters:
        - record (logging.LogRecord): The log record instance containing message, level, timestamp, etc.

        Returns:
        - str: The fully formatted, colorized log message string ready for output to console.
        """
        log_fmt = '%(asctime)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        formatted = formatter.format(record)
        color = self.colorcodes.get(record.levelno, "")
        return f"{color}{formatted}{self.resetcode}"


# Function 'LogShow'
def LogShow():
    """
    Initializes and configures the root logger to output log messages to the console using
    a custom, color-enhanced formatting scheme. This function replaces any existing stream
    handlers with a new one configured using the LogFormat class, which applies ANSI color
    codes to log messages based on severity levels. The global logging level is set to INFO,
    ensuring that all relevant operational events are printed during execution.

    Parameters:
    - None

    Returns:
    - None
    """
    handler = logging.StreamHandler()
    handler.setFormatter(LogFormat())
    logging.getLogger().handlers = [handler]
    logging.getLogger().setLevel(logging.INFO)


# Function 'LogSave'
def LogSave(botname: str):
    """
    Configures file-based logging for the current process using the specified bot name
    as the identifier for the log file. The log file is created inside a 'logs' directory,
    which is generated if it does not already exist. If a file handler for the same file
    already exists, the function avoids adding it again. This ensures all logs are saved
    persistently with a consistent timestamped format for later analysis and debugging.

    Parameters:
    - botname (str): The name of the bot, used to name the log file (e.g., 'mybot.log').

    Returns:
    - None
    """
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / f"{botname}.log"
    logger = logging.getLogger()

    if any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file) for h in logger.handlers):
        return

    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)