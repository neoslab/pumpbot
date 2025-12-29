# Import libraries
import requests
import time


# Class 'SolPrice'
class SolPrice:
    """ Class description """
    
    # Define 'solprice'
    solprice = None

    # Define 'lastfetch'
    lastfetch = 0

    # Define 'ttl'
    ttl = 60

    # Function 'solvsusd'
    @classmethod
    def solvsusd(cls):
        """ Function description """
        now = time.time()
        if cls.solprice is None or now - cls.lastfetch > cls.ttl:
            try:
                url = "https://api.coingecko.com/api/v3/simple/price"
                params = {"ids": "solana", "vs_currencies": "usd"}
                response = requests.get(url, params=params, timeout=5)
                response.raise_for_status()
                data = response.json()
                cls.solprice = float(data["solana"]["usd"])
                cls.lastfetch = now
            except Exception as e:
                print(f"[CoinGecko Error] Failed to fetch SOL price: {e}")
        return cls.solprice