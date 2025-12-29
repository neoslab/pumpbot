# Import packages
from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.sql import func
from sqlalchemy import String
from sqlalchemy.orm import declarative_base

# SQLAlchemy setup
PumpBase = declarative_base()


# Class 'PumpTableTokens'
class PumpTableTokens(PumpBase):
    """ Class description """
    __tablename__ = 'tokens'
    id = Column(Integer, primary_key=True, autoincrement=True)
    created = Column(BigInteger, index=True)
    mint = Column(String, index=True, nullable=False)
    name = Column(String, index=True)
    symbol = Column(String, index=True)
    owner = Column(String, index=True)
    price = Column(String)
    liquidity = Column(String)
    volume = Column(String)
    marketcap = Column(String)
    lastorder = Column(BigInteger)
    twitter = Column(String)
    telegram = Column(String)
    website = Column(String)


# Class 'PumpTableTrades'
class PumpTableTrades(PumpBase):
    """ Class description """
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True, autoincrement=True)
    created = Column(DateTime(timezone=True), server_default=func.now())
    mint = Column(String, ForeignKey('tokens.mint'), index=True, nullable=False)
    uuid = Column(String, nullable=False, index=True)
    bot = Column(String, nullable=False, index=True)
    start = Column(BigInteger, index=True, nullable=False)
    stop = Column(BigInteger, index=True)
    duration = Column(BigInteger)
    open = Column(String)
    close = Column(String)
    amount = Column(String)
    total = Column(String)
    profit = Column(String)
    ratio = Column(String)
    signature = Column(String)
    status = Column(String, default='OPEN', index=True)

# Class 'PumpTableWallet'
class PumpTableWallet(PumpBase):
    """ Class description """
    __tablename__ = 'wallet'
    id = Column(Integer, primary_key=True, default=1)
    balance = Column(String, nullable=False)