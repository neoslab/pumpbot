# === Import packages ===
import datetime
import re
import uuid

# === Class 'ScriptUtils' ===
class ScriptUtils:
    """
    The ScriptUtils class provides utility functions that can be used across various
    modules of a software system. It is designed as a collection of static tools
    that perform common low-level tasks such as UUID generation. The class does not
    require instantiation and is intended to be accessed statically, making it ideal
    for simple operations that don't require maintaining state.

    Parameters:
    - None (All methods are static and require no class instantiation.)

    Returns:
    - None
    """

    # === Function 'uuidgen' ===
    @staticmethod
    def uuidgen() -> str:
        """
        Generates a new universally unique identifier (UUID) using version 4 of the
        UUID specification, which creates a random UUID. This function is typically
        used for generating unique keys, tracking identifiers, or ensuring data
        uniqueness in distributed systems or databases. The UUID is returned as a
        string in standard 8-4-4-4-12 hexadecimal format.

        Parameters:
        - None

        Returns:
        - str: A version 4 UUID string in the format xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.
        """
        return str(uuid.uuid4())

    # === Function 'safedatetime' ===
    @staticmethod
    def safedatetime(ts):
        """ Function description """
        try:
            ts = int(ts)
            if ts <= 0 or ts > 2147483647:
                return "n/a"
            return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        except (TypeError, ValueError):
            return "n/a"

    # === Function 'stripansi' ===
    @staticmethod
    def stripansi(text: str) -> str:
        """ Function description """
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    @staticmethod
    # === Function 'unixtodatetime' ===
    def unixtodatetime(value):
        """ Function description """
        try:
            return datetime.datetime.fromtimestamp(float(value)).strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError, OSError, OverflowError):
            return ''