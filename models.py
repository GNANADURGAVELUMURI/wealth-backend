from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

    goals = relationship("Goal", back_populates="user")
    investments = relationship("Investment", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    goal_transactions = relationship("GoalTransaction", back_populates="user")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    goal_type = Column(String)
    target_amount = Column(Float)
    target_date = Column(DateTime)
    monthly_contribution = Column(Float)
    status = Column(String, default="Active")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="goals")
    goal_transactions = relationship("GoalTransaction", back_populates="goal")


class GoalTransaction(Base):
    __tablename__ = "goal_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    goal_id = Column(Integer, ForeignKey("goals.id"))
    contribution = Column(Float)
    executed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="goal_transactions")
    goal = relationship("Goal", back_populates="goal_transactions")





class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    asset_type = Column(String)
    symbol = Column(String)
    units = Column(Float)
    avg_buy_price = Column(Float)
    cost_basis = Column(Float)
    current_value = Column(Float)
    last_price = Column(Float)
    last_price_at = Column(DateTime)
    status = Column(String, default="ACTIVE")

    user = relationship("User", back_populates="investments")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    symbol = Column(String)
    type = Column(String)  # BUY / SELL
    quantity = Column(Float)
    price = Column(Float)
    fees = Column(Float, default=0)
    executed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")


