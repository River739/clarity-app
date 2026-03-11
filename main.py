from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import Transaction
from classifier import classify_merchant
import re

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# SMS Parser function
def parse_upi_sms(sms: str):
    result = {
        "amount": None,
        "merchant": None,
        "bank_name": None,
        "transaction_type": None,
        "raw_sms": sms
    }

    # Detect transaction type
    if any(word in sms.lower() for word in ["debited", "debit", "spent", "paid"]):
        result["transaction_type"] = "debit"
    elif any(word in sms.lower() for word in ["credited", "credit", "received"]):
        result["transaction_type"] = "credit"

    # Extract amount
    amount_match = re.search(r'(?:rs\.?|inr)\s*([\d,]+\.?\d*)', sms.lower())
    if amount_match:
        result["amount"] = float(amount_match.group(1).replace(',', ''))

    # Extract merchant from UPI info
    merchant_match = re.search(r'(?:upi/|to\s+|at\s+)([a-zA-Z0-9\s]+?)(?:\.|/|$)', sms, re.IGNORECASE)
    if merchant_match:
        result["merchant"] = merchant_match.group(1).strip()

    # Detect bank
    if "hdfc" in sms.lower():
        result["bank_name"] = "HDFC"
    elif "sbi" in sms.lower():
        result["bank_name"] = "SBI"
    elif "icici" in sms.lower():
        result["bank_name"] = "ICICI"
    else:
        result["bank_name"] = "Unknown"

    return result

# Routes
@app.get("/")
def root():
    return {"message": "Clarity API is running"}

@app.post("/parse-sms")
def parse_sms(sms: dict, db: Session = Depends(get_db)):
    parsed = parse_upi_sms(sms["text"])
    
    category = classify_merchant(parsed["merchant"])

    transaction = Transaction(
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
def get_transactions(db: Session = Depends(get_db)):
    transactions = db.query(Transaction).all()
    return {"count": len(transactions), "transactions": [
        {
            "id": t.id,
            "bank": t.bank_name,
            "amount": t.amount,
            "merchant": t.merchant,
            "type": t.transaction_type,
            "timestamp": t.timestamp
        } for t in transactions
    ]}