from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String)
    amount = Column(Float)
    merchant = Column(String)
    category = Column(String, default="Uncategorized")
    transaction_type = Column(String)  # debit or credit
    timestamp = Column(DateTime, server_default=func.now())
    raw_sms = Column(String)