from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    transactions = relationship("Transaction", back_populates="user")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    bank_name = Column(String)
    amount = Column(Float)
    merchant = Column(String)
    category = Column(String, default="Uncategorized")
    transaction_type = Column(String)
    timestamp = Column(DateTime, server_default=func.now())
    raw_sms = Column(String)
    user = relationship("User", back_populates="transactions")

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category = Column(String)
    monthly_limit = Column(Float)
    alert_threshold = Column(Float, default=0.8)
    created_at = Column(DateTime, server_default=func.now())