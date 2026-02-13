from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

# ---------- USERS ----------
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    class Config:
        from_attributes = True


# ---------- GOALS ----------
class GoalCreate(BaseModel):
    goal_type: str
    target_amount: float
    target_date: date
    monthly_contribution: float
    status: str
    user_id: int

class GoalResponse(GoalCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ---------- GOAL TRANSACTIONS ----------
class GoalTransactionCreate(BaseModel):
    user_id: int
    goal_id: int
    contribution: float

class GoalTransactionResponse(GoalTransactionCreate):
    id: int
    executed_at: datetime
    class Config:
        from_attributes = True


# ---------- INVESTMENTS ----------
class InvestmentResponse(BaseModel):
    id: int
    user_id: int
    asset_type: str
    symbol: str
    units: float
    avg_buy_price: float
    cost_basis: float
    current_value: float
    last_price: float
    last_price_at: datetime
    status: str
    class Config:
        from_attributes = True


# ---------- TRANSACTIONS ----------
class TransactionCreate(BaseModel):
    symbol: str
    type: str
    quantity: float
    fees: Optional[float] = 0
    user_id: int

class TransactionResponse(TransactionCreate):
    id: int
    price: float
    executed_at: datetime
    class Config:
        from_attributes = True
