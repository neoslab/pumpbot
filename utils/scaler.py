# === Import packages ===
from decimal import Decimal
from decimal import InvalidOperation

# Define 'LAMPORTS_PER_SOL'
LAMPORTS_PER_SOL = 1_000_000_000


# === Class 'NumberScaler' ===
class NumberScaler:
    """
    The NumberScaler class provides utility methods for formatting and safely converting
    numeric values in financial or trading contexts. Its primary purpose is to present
    floating-point or string-based numeric inputs in a readable and consistent format,
    while gracefully handling malformed or invalid inputs. This class includes methods
    for displaying prices with appropriate decimal precision and for converting values
    into `Decimal` objects for higher-precision computations or arithmetic operations.

    Parameters:
    - None (All methods are static and the class does not require instantiation.)

    Returns:
    - None
    """

    # === Function 'convertlamports' ===
    @staticmethod
    def convertlamports(value):
        """
        Converts a given value from lamports to SOL (Solana's main token unit) using the
        predefined constant `LAMPORTS_PER_SOL`. This function handles string, integer,
        or float inputs and returns the equivalent SOL value rounded to 9 decimal places.
        It gracefully handles invalid inputs such as None or non-numeric types and returns
        0.0 in such cases, ensuring the program remains stable during conversion operations.

        Parameters:
        - value (any): The amount in lamports to be converted into SOL. Accepts str, int, or float.

        Returns:
        - float: The SOL-equivalent value rounded to 9 decimal places, or 0.0 if conversion fails.
        """
        try:
            return round(float(value) / LAMPORTS_PER_SOL, 9)
        except (TypeError, ValueError):
            return 0.0

    # === Function 'safefloat' ===
    @staticmethod
    def safefloat(ms):
        """
        Converts the given input to a float and returns the result in seconds by dividing
        it by 1000. This method is intended for converting millisecond-based timing values
        to seconds, which are often used in asynchronous sleeps or timeout handling. If
        the input is invalid (non-numeric, None, or <= 0), it returns False to indicate
        that the conversion was unsuccessful or not applicable.

        Parameters:
        - ms (any): The input value representing time in milliseconds. It can be a string, int, or float.

        Returns:
        - float: The time in seconds (converted from milliseconds) if the input is valid and > 0.
        - bool: Returns False if the input is invalid or not a positive number.
        """
        try:
            ms = float(ms)
            if ms > 0:
                return ms / 1000.0
            else:
                return False
        except (ValueError, TypeError):
            return False

    # === Function 'showprice' ===
    @staticmethod
    def showprice(value) -> str:
        """
        Converts a numeric value into a formatted string representation suitable for display
        in price fields. This function automatically adjusts the number of decimal places
        based on the magnitude of the input value to enhance readability. It supports string,
        float, and integer inputs, and provides a fallback of "0" if parsing fails.

        Parameters:
        - value (any): A numeric value or string that represents a number to format as a price.

        Returns:
        - str: A string-formatted price with 2, 4, 6, or 10 decimal places depending on magnitude.
        """
        try:
            price = float(value)
        except (ValueError, TypeError):
            return "0"

        if price >= 1:
            return f"{price:,.2f}"
        elif price >= 0.01:
            return f"{price:.4f}"
        elif price >= 0.0001:
            return f"{price:.6f}"
        else:
            return f"{price:.10f}"

    # === Function 'convertdecimal' ===
    @staticmethod
    def convertdecimal(value) -> Decimal:
        """
        Converts any string or numeric input into a `Decimal` object for high-precision arithmetic.
        It ensures that formatting artifacts such as commas are removed from string inputs before
        conversion. If the input is malformed or an exception is raised during parsing, the function
        safely returns a default `Decimal(0)` instead of crashing the application.

        Parameters:
        - value (any): A numeric or string input representing a number to convert into a Decimal.

        Returns:
        - Decimal: A Decimal object representing the numeric input, or Decimal(0) if conversion fails.
        """
        try:
            if isinstance(value, str):
                return Decimal(value.replace(",", ""))
            return Decimal(str(value))
        except (InvalidOperation, TypeError, AttributeError):
            return Decimal(0)

    # === Function 'formatsuffix' ===
    @staticmethod
    def formatsuffix(value):
        """ Function description """
        try:
            num = float(value)
            if num >= 1_000_000_000:
                return f"{num / 1_000_000_000:.2f}B"
            elif num >= 1_000_000:
                return f"{num / 1_000_000:.2f}M"
            elif num >= 1_000:
                return f"{num / 1_000:.2f}K"
            else:
                return f"{num:.2f}"
        except (TypeError, ValueError):
            return "n/a"

    @staticmethod
    # === Function 'formatdecimal' ===
    def formatdecimal(value, decimals=10):
        """ Function description """
        try:
            formatstr = "{:,.{dec}f}".format(float(value), dec=decimals)
            return formatstr
        except (ValueError, TypeError):
            return 'N/A'
