# Import packages
from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy.orm import declarative_base

# SQLAlchemy setup
PumpBase = declarative_base()


# Class 'PumpFunDB'
class PumpFunDB(PumpBase):
    """ Class description """
    __tablename__ = 'pumpfun'
    mint = Column(String, primary_key=True)
    name = Column(String)
    symbol = Column(String)
    created = Column(BigInteger, index=True)
    owner = Column(String, index=True)
    price = Column(String)
    liquidity = Column(Numeric(20, 9))
    volume = Column(String)
    marketcap = Column(Numeric(20, 9))
    lastorder = Column(BigInteger)
    twitter = Column(String)
    telegram = Column(String)
    website = Column(String)