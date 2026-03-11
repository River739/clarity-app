from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MERCHANT_CATEGORIES = {
    # Food
    "swiggy": "Food", "zomato": "Food", "dominos": "Food",
    "mcdonalds": "Food", "kfc": "Food", "subway": "Food",
    "dunzo": "Food", "blinkit": "Food",

    # Transport
    "ola": "Transport", "uber": "Transport", "rapido": "Transport",
    "irctc": "Transport", "redbus": "Transport", "makemytrip": "Transport",

    # Shopping
    "amazon": "Shopping", "flipkart": "Shopping", "myntra": "Shopping",
    "ajio": "Shopping", "meesho": "Shopping", "nykaa": "Shopping",

    # Subscriptions
    "netflix": "Subscriptions", "spotify": "Subscriptions",
    "prime": "Subscriptions", "hotstar": "Subscriptions",
    "youtube": "Subscriptions", "zee5": "Subscriptions",

    # Utilities
    "bescom": "Utilities", "bsnl": "Utilities", "airtel": "Utilities",
    "jio": "Utilities", "vodafone": "Utilities", "tata": "Utilities",

    # Health
    "pharmeasy": "Health", "1mg": "Health", "apollo": "Health",
    "netmeds": "Health",

    # Education
    "udemy": "Education", "coursera": "Education", "unacademy": "Education",
    "byjus": "Education",
}

def classify_merchant(merchant: str) -> str:
    if not merchant:
        return "Uncategorized"

    merchant_lower = merchant.lower()
    for key, category in MERCHANT_CATEGORIES.items():
        if key in merchant_lower:
            return category

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial transaction classifier for Indian users. Reply with ONLY one category name, nothing else."
                },
                {
                    "role": "user",
                    "content": f"""Classify this merchant into exactly ONE of these categories:
Food, Transport, Shopping, Subscriptions, Utilities, Health, Education, Entertainment, Transfer, EMI, Other

Merchant name: {merchant}"""
                }
            ],
            max_tokens=10,
            temperature=0
        )

        category = response.choices[0].message.content.strip()
        print(f"Groq returned: {category}")

        valid_categories = ["Food", "Transport", "Shopping", "Subscriptions",
                          "Utilities", "Health", "Education", "Entertainment",
                          "Transfer", "EMI", "Other"]
        if category in valid_categories:
            return category
        return "Other"

    except Exception as e:
        print(f"Groq classification failed: {e}")
        return "Uncategorized"