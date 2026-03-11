from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import Transaction, User, Budget
from classifier import classify_merchant
from auth import hash_password, verify_password, create_access_token, get_current_user
from pydantic import BaseModel
import re

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clarity API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Schemas ---
class UserRegister(BaseModel):
    email: str
    name: str
    password: str

class SMSInput(BaseModel):
    text: str

class BudgetInput(BaseModel):
    category: str
    monthly_limit: float
    alert_threshold: float = 0.8

# --- SMS Parser ---
def parse_upi_sms(sms: str):
    result = {
        "amount": None,
        "merchant": None,
        "bank_name": None,
        "transaction_type": None,
        "raw_sms": sms
    }

    if any(word in sms.lower() for word in ["debited", "debit", "spent", "paid"]):
        result["transaction_type"] = "debit"
    elif any(word in sms.lower() for word in ["credited", "credit", "received"]):
        result["transaction_type"] = "credit"

    amount_match = re.search(r'(?:rs\.?|inr)\s*([\d,]+\.?\d*)', sms.lower())
    if amount_match:
        result["amount"] = float(amount_match.group(1).replace(',', ''))

    merchant_match = re.search(r'(?:upi/|to\s+|at\s+)([a-zA-Z0-9\s]+?)(?:\.|/|$)', sms, re.IGNORECASE)
    if merchant_match:
        result["merchant"] = merchant_match.group(1).strip()

    if "hdfc" in sms.lower():
        result["bank_name"] = "HDFC"
    elif "sbi" in sms.lower():
        result["bank_name"] = "SBI"
    elif "icici" in sms.lower():
        result["bank_name"] = "ICICI"
    elif "axis" in sms.lower():
        result["bank_name"] = "Axis"
    elif "kotak" in sms.lower():
        result["bank_name"] = "Kotak"
    else:
        result["bank_name"] = "Unknown"

    return result

# --- Routes ---
@app.get("/")
def root():
    return {"message": "Clarity API is running"}

@app.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=data.email,
        name=data.name,
        hashed_password=hash_password(data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "name": user.name}

@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "name": user.name}

@app.post("/parse-sms")
def parse_sms(sms: SMSInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    parsed = parse_upi_sms(sms.text)
    category = classify_merchant(parsed["merchant"])

    transaction = Transaction(
        user_id=current_user.id,
        bank_name=parsed["bank_name"],
        amount=parsed["amount"],
        merchant=parsed["merchant"],
        category=category,
        transaction_type=parsed["transaction_type"],
        raw_sms=parsed["raw_sms"]
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return {
        "message": "Transaction saved",
        "data": {
            "id": transaction.id,
            "bank": transaction.bank_name,
            "amount": transaction.amount,
            "merchant": transaction.merchant,
            "category": transaction.category,
            "type": transaction.transaction_type
        }
    }

@app.get("/transactions")
def get_transactions(bank: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if bank:
        query = query.filter(Transaction.bank_name == bank)
    transactions = query.order_by(Transaction.timestamp.desc()).all()
    return {
        "count": len(transactions),
        "transactions": [
            {
                "id": t.id,
                "bank": t.bank_name,
                "amount": t.amount,
                "merchant": t.merchant,
                "category": t.category,
                "type": t.transaction_type,
                "timestamp": t.timestamp
            } for t in transactions
        ]
    }

@app.post("/budgets")
def create_budget(data: BudgetInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    budget = Budget(
        user_id=current_user.id,
        category=data.category,
        monthly_limit=data.monthly_limit,
        alert_threshold=data.alert_threshold
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return {"message": "Budget created", "budget_id": budget.id}

@app.get("/summary")
def get_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    transactions = db.query(Transaction).filter(Transaction.user_id == current_user.id).all()
    
    summary = {}
    total_spent = 0
    banks = set()

    for t in transactions:
        if t.transaction_type == "debit":
            total_spent += t.amount or 0
            summary[t.category] = summary.get(t.category, 0) + (t.amount or 0)
        if t.bank_name:
            banks.add(t.bank_name)

    return {
        "total_spent": total_spent,
        "total_transactions": len(transactions),
        "banks": list(banks),
        "spending_by_category": summary
    }