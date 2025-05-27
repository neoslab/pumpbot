# Import libraries
import os
import requests

# Import packages
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Import dependencies
from utils.model import PumpBase
from utils.model import PumpFunDB

# Define 'LAMPORTS_PER_SOL'
LAMPORTS_PER_SOL = 1_000_000_000


# Class 'PumpFunScreener'
class PumpFunScreener:
    """ Class description """

    # Class initialization
    def __init__(self):
        """ Initializer description """
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        db_folder = os.path.join(project_root, "database")
        os.makedirs(db_folder, exist_ok=True)

        db_path = os.path.join(db_folder, "pumpfun.db")
        db_url = f"sqlite:///{db_path}"

        self.engine = create_engine(db_url)
        PumpBase.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    # Function 'from_lamports'
    @staticmethod
    def fromlamport(value):
        """ Function description """
        try:
            return round(float(value) / LAMPORTS_PER_SOL, 9)
        except (TypeError, ValueError):
            print(f"[fromlamport] Invalid value: {value}")
            return 0.0

    # Function 'formatprice'
    @staticmethod
    def formatprice(quotedprice):
        """ Function description """
        if quotedprice >= 1:
            return f"{quotedprice:,.2f}"
        elif quotedprice >= 0.01:
            return f"{quotedprice:.4f}"
        elif quotedprice >= 0.0001:
            return f"{quotedprice:.6f}"
        else:
            return f"{quotedprice:.8f}"

    # Function 'extractprice'
    def extractprice(self, mint):
        """ Function description """
        url = f"https://swap-api.pump.fun/v1/coins/{mint}/candles?interval=1s&currency=USD&limit=1"
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            tokeninfo = r.json()
            if not tokeninfo:
                return False
            priceclose = float(tokeninfo[0]["close"])
            marketvolume = float(tokeninfo[0]["volume"])
            tokenprice = self.formatprice(priceclose)
            tokenvolume = f"{marketvolume:,.2f}"
            return priceclose, tokenprice, tokenvolume
        except (requests.RequestException, ValueError, KeyError):
            return False

    # Function 'extractdata'
    def extractdata(self, mint):
        """ Function description """
        url = f"https://frontend-api-v3.pump.fun/coins/{mint}"
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            tokeninfo = r.json()
            return (
                tokeninfo.get("name"),
                tokeninfo.get("symbol"),
                int(int(tokeninfo.get("created_timestamp") or 0) / 1000),
                tokeninfo.get("creator"),
                self.fromlamport(tokeninfo.get("real_sol_reserves")),
                float(tokeninfo.get("market_cap", 0)),
                int(int(tokeninfo.get("last_trade_timestamp") or 0) / 1000),
                tokeninfo.get("twitter"),
                tokeninfo.get("telegram"),
                tokeninfo.get("website")
            )
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"Error: {e}")
            return False

    # Function 'tokenquery'
    def tokenquery(self, mint):
        """ Function description """
        session = self.Session()
        try:
            exists = session.query(PumpFunDB).filter_by(mint=mint).first()
            if exists:
                print("Token already in database.")
                return

            result = self.extractprice(mint)
            if not result:
                print("Failed to retrieve token price.")
                return

            token = self.extractdata(mint)
            if not token:
                print("Failed to retrieve token metadata.")
                return

            priceclose, tokenprice, tokenvolume = result
            (
                tokenname,
                tokensymbol,
                tokencreated,
                tokenowner,
                tokenliquidity,
                tokenmarketcap,
                tokenlastorder,
                tokentwitter,
                tokentelegram,
                tokenwebsite
            ) = token

            if tokenliquidity == 0.0:
                print("Skipping token with zero pool.")
                return

            token_entry = PumpFunDB(
                mint = mint,
                name = tokenname,
                symbol = tokensymbol,
                created = tokencreated,
                owner = tokenowner,
                price = tokenprice,
                liquidity = Decimal(str(tokenliquidity)),
                volume = tokenvolume,
                marketcap = Decimal(str(tokenmarketcap)),
                lastorder = tokenlastorder,
                twitter = tokentwitter,
                telegram = tokentelegram,
                website = tokenwebsite
            )
            session.add(token_entry)
            session.commit()

        except SQLAlchemyError as e:
            session.rollback()
            print("Database error:", e)
        finally:
            session.close()
