from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

import models
import schemas
from database import get_db
from services.marketprice import get_live_price
from fastapi.responses import JSONResponse
from celery_tasks import refresh_investments_task




app = FastAPI()

# ===================== CORS =====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =================================================
# ===================== USERS =====================
# =================================================

@app.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        name=user.name,
        email=user.email,
        password=user.password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=schemas.UserResponse)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return db_user


@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users", response_model=list[schemas.UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


# =================================================
# ===================== GOALS =====================
# =================================================

@app.post("/goals", response_model=schemas.GoalResponse)
def create_goal(goal: schemas.GoalCreate, db: Session = Depends(get_db)):
    new_goal = models.Goal(
        goal_type=goal.goal_type,
        target_amount=goal.target_amount,
        target_date=goal.target_date,
        monthly_contribution=goal.monthly_contribution,
        status=goal.status,
        user_id=goal.user_id
    )
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return new_goal


@app.get("/goals/{user_id}", response_model=list[schemas.GoalResponse])
def get_goals(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Goal).filter(
        models.Goal.user_id == user_id
    ).all()


@app.put("/goals/{goal_id}", response_model=schemas.GoalResponse)
def update_goal(goal_id: int, goal: schemas.GoalCreate, db: Session = Depends(get_db)):
    db_goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == goal.user_id
    ).first()

    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    db_goal.goal_type = goal.goal_type
    db_goal.target_amount = goal.target_amount
    db_goal.target_date = goal.target_date
    db_goal.monthly_contribution = goal.monthly_contribution
    db_goal.status = goal.status

    db.commit()
    db.refresh(db_goal)
    return db_goal


@app.delete("/goals/{goal_id}")
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    goal = db.query(models.Goal).filter(models.Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    db.delete(goal)
    db.commit()
    return {"message": "Goal deleted successfully"}


# ---------------- GOAL PROGRESS ----------------

@app.get("/goals/progress/{goal_id}")
def goal_progress(goal_id: int, db: Session = Depends(get_db)):
    total_paid = (
        db.query(func.coalesce(func.sum(models.GoalTransaction.contribution), 0))
        .filter(models.GoalTransaction.goal_id == goal_id)
        .scalar()
    )
    return {"total_paid": total_paid}


# ---------------- GOAL TRANSACTIONS ----------------

@app.post("/goal-transactions", response_model=schemas.GoalTransactionResponse)
def create_goal_transaction(
    tx: schemas.GoalTransactionCreate,
    db: Session = Depends(get_db)
):
    goal = db.query(models.Goal).filter(
        models.Goal.id == tx.goal_id,
        models.Goal.user_id == tx.user_id
    ).first()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    new_tx = models.GoalTransaction(
        user_id=tx.user_id,
        goal_id=tx.goal_id,
        contribution=tx.contribution,
        executed_at=datetime.utcnow()
    )

    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)
    return new_tx


@app.get("/goal-transactions/{user_id}", response_model=list[schemas.GoalTransactionResponse])
def get_goal_transactions(user_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.GoalTransaction)
        .filter(models.GoalTransaction.user_id == user_id)
        .order_by(models.GoalTransaction.executed_at.desc())
        .all()
    )


# =================================================
# ================== INVESTMENTS ==================
# =================================================

@app.post("/investments/refresh/{user_id}")
def refresh(user_id: int):
    refresh_investments_task.delay(user_id)
    return {
        "message": "Investment refresh started in background"
    }

@app.get("/investments/{user_id}", response_model=list[schemas.InvestmentResponse])
def get_investments(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Investment).filter(
        models.Investment.user_id == user_id
    ).all()


@app.get("/investments/refresh/{user_id}")
def refresh_investments(user_id: int, db: Session = Depends(get_db)):
    investments = db.query(models.Investment).filter(
        models.Investment.user_id == user_id,
        models.Investment.status == "ACTIVE"
    ).all()

    updated = []

    for inv in investments:
        try:
            price = get_live_price(inv.symbol)

            inv.last_price = price
            inv.current_value = round(inv.units * price, 2)
            inv.last_price_at = datetime.utcnow()

            updated.append(inv.symbol)

        except Exception as e:
            print(f"Skipping {inv.symbol}: {e}")

    db.commit()   # 🔥 MOST IMPORTANT LINE

    return {
        "message": "Prices refreshed",
        "updated_symbols": updated
    }



@app.delete("/investments/{id}")
def delete_investment(id: int, db: Session = Depends(get_db)):
    inv = db.query(models.Investment).filter(models.Investment.id == id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")

    db.delete(inv)
    db.commit()
    return {"message": "Investment deleted"}


# =================================================
# ================= TRANSACTIONS ==================
# =================================================

@app.post("/transactions", response_model=schemas.TransactionResponse)
def create_transaction(tx: schemas.TransactionCreate, db: Session = Depends(get_db)):

    symbol = tx.symbol.strip().upper()
    tx_type = tx.type.upper()

    try:
        live_price = get_live_price(symbol)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    if live_price == 0:
        raise HTTPException(
            status_code=400,
            detail="Live price unavailable. Use correct symbol (e.g. ITC.BSE)"
        )

    new_tx = models.Transaction(
        symbol=symbol,
        type=tx_type,
        quantity=tx.quantity,
        price=live_price,
        fees=tx.fees,
        user_id=tx.user_id,
        executed_at=datetime.utcnow()
    )
    db.add(new_tx)

    inv = db.query(models.Investment).filter(
        models.Investment.user_id == tx.user_id,
        models.Investment.symbol == symbol
    ).first()

    if tx_type == "BUY":
        if inv:
            total_units = inv.units + tx.quantity
            total_cost = inv.cost_basis + (tx.quantity * live_price)

            inv.units = total_units
            inv.cost_basis = total_cost
            inv.avg_buy_price = total_cost / total_units
        else:
            inv = models.Investment(
                user_id=tx.user_id,
                asset_type="AUTO",
                symbol=symbol,
                units=tx.quantity,
                avg_buy_price=live_price,
                cost_basis=tx.quantity * live_price,
                current_value=tx.quantity * live_price,
                last_price=live_price,
                last_price_at=datetime.utcnow(),
                status="ACTIVE"
            )
            db.add(inv)

    elif tx_type == "SELL":
        if not inv or tx.quantity > inv.units:
            raise HTTPException(status_code=400, detail="Invalid SELL request")

        inv.units -= tx.quantity
        inv.cost_basis -= inv.avg_buy_price * tx.quantity
        if inv.units == 0:
            inv.status = "INACTIVE"

    inv.last_price = live_price
    inv.current_value = inv.units * live_price
    inv.last_price_at = datetime.utcnow()

    db.commit()
    db.refresh(new_tx)
    return new_tx


@app.get("/transactions/{user_id}", response_model=list[schemas.TransactionResponse])
def get_transactions(user_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == user_id)
        .order_by(models.Transaction.executed_at.desc())
        .all()
    )


@app.delete("/transactions/{tx_id}")
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(tx)
    db.commit()
    return {"message": "Transaction deleted"}


# =================================================
# ================= MARKET PRICE ==================
# =================================================

@app.get("/market-price/{symbol}")
def market_price(symbol: str):
    try:
        price = get_live_price(symbol)
        return {"symbol": symbol.upper(), "price": price}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
def root():
    return {"status": "Backend running"}
    
@app.post("/investments/refresh/{user_id}")
def refresh(user_id: int):
    refresh_investments_task.delay(user_id)
    return {
        "message": "Investment refresh started in background"
    }

