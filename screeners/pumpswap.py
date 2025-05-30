# Import libraries
import logging
import os
import requests

# Import packages
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

# Import dependencies
from utils.models import PumpBase
from utils.models import PumpTableTokens
from utils.scaler import NumberScaler

# Define 'logger'
logger = logging.getLogger(__name__)

# Define 'LAMPORTS_PER_SOL'
LAMPORTS_PER_SOL = 1_000_000_000


# Class 'PumpScreener'
class PumpScreener:
    """ Class description """

    # Class initialization
    def __init__(self):
        """ Initializer description """
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        db_folder = os.path.join(project_root, "database")
        os.makedirs(db_folder, exist_ok=True)

        db_path = os.path.join(db_folder, "tokens.db")
        db_url = f"sqlite:///{db_path}"

        self.engine = create_engine(db_url)
        PumpBase.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    # Function 'extractprice'
    @staticmethod
    def extractprice(mint):
        """ Function description """
        url = f"https://swap-api.pump.fun/v1/coins/{mint}/candles?interval=1s&limit=1&currency=USD"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
            "Connection": "close"
        }
        try:
            with requests.Session() as s:
                s.headers.update(headers)
                r = s.get(url, timeout=5)
                r.raise_for_status()
                tokeninfo = r.json()
                if not tokeninfo:
                    return False
                priceclose = float(tokeninfo[0]["close"])
                marketvolume = float(tokeninfo[0]["volume"])
                tokenprice = NumberScaler.showprice(priceclose)
                tokenvolume = f"{marketvolume:,.2f}"
                return priceclose, tokenprice, tokenvolume
        except requests.HTTPError:
            return False
        except (requests.RequestException, ValueError, KeyError):
            return False

    # Function 'extractdata'
    @staticmethod
    def extractdata(mint):
        """ Function description """
        url = f"https://frontend-api-v3.pump.fun/coins/{mint}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
            "Connection": "close"
        }
        try:
            with requests.Session() as s:
                s.headers.update(headers)
                r = s.get(url, timeout=5)
                r.raise_for_status()
                tokeninfo = r.json()
                return (
                    int(int(tokeninfo.get("created_timestamp") or 0) / 1000),
                    tokeninfo.get("name"),
                    tokeninfo.get("symbol"),
                    tokeninfo.get("creator"),
                    NumberScaler.convertlamports(tokeninfo.get("real_sol_reserves")),
                    float(tokeninfo.get("market_cap", 0)),
                    int(int(tokeninfo.get("last_trade_timestamp") or 0) / 1000),
                    tokeninfo.get("twitter"),
                    tokeninfo.get("telegram"),
                    tokeninfo.get("website")
                )
        except requests.HTTPError:
            return False
        except (requests.RequestException, ValueError, KeyError):
            return False

    # Function 'tokenquery'
    def tokenquery(self, mint):
        """Query token data, insert to DB if new, and return financial metrics"""
        session = self.Session()
        try:
            # Check if token already exists
            exists = session.query(PumpTableTokens).filter_by(mint=mint).first()
            if exists:
                logger.error(f"Skipping {mint} token already present in database.")
                return {
                    "price": str(exists.price or 0),
                    "liquidity": str(exists.liquidity or 0),
                    "volume": str(exists.volume or 0),
                    "marketcap": str(exists.marketcap or 0)
                }

            # Get live price and metadata
            result = self.extractprice(mint)
            if not result:
                logger.error(f"Skipping {mint} failed to retrieve token price.")
                return None

            token = self.extractdata(mint)
            if not token:
                logger.error(f"Skipping {mint} failed to retrieve token metadata.")
                return None

            priceclose, tokenprice, tokenvolume = result
            (
                tokencreated,
                tokenname,
                tokensymbol,
                tokenowner,
                tokenliquidity,
                tokenmarketcap,
                tokenlastorder,
                tokentwitter,
                tokentelegram,
                tokenwebsite
            ) = token

            if tokenliquidity == 0.0:
                logger.error(f"Skipping {mint} due to no liquidity.")
                return None

            # Store in DB
            token_entry = PumpTableTokens(
                created=tokencreated,
                mint=mint,
                name=tokenname,
                symbol=tokensymbol,
                owner=tokenowner,
                price=tokenprice,
                liquidity=tokenliquidity,
                volume=tokenvolume,
                marketcap=tokenmarketcap,
                lastorder=tokenlastorder,
                twitter=tokentwitter,
                telegram=tokentelegram,
                website=tokenwebsite
            )
            session.add(token_entry)
            session.commit()

            # Return structured data
            return {
                "created": int(tokencreated or 0),
                "price": str(priceclose or 0),
                "liquidity": str(tokenliquidity or 0),
                "volume": str(tokenvolume or 0),
                "marketcap": str(tokenmarketcap or 0)
            }

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {e!s}")
            return None
        finally:
            session.close()